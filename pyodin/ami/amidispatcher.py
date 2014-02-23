import os
import sys
import re
import time
import logging
import optparse
from commons import BasicObject, BasicObjectEncoder, OdinConfigParser

logging.DUMPOBJECTS = False

logger = logging.getLogger("odin_ami");

from ConfigParser import SafeConfigParser, NoOptionError

try:
    from twisted.python import failure
    from twisted.internet import reactor, task, defer
    from twisted.internet import error as tw_error
    from twisted.web import resource
except ImportError:
    print "AMIWORKER ERROR: Module twisted not found."
    print "You need twisted matrix 10.1+ to run AMIWORKER. Get it from http://twistedmatrix.com/"
    sys.exit(1)

try:
    from starpy import manager
    from starpy.error import AMICommandFailure
except ImportError:
    print "AMIWORKER ERROR: Module starpy not found."
    print "You need starpy to run AMIWORKER. Get it from http://www.vrplumber.com/programming/starpy/"
    sys.exit(1)
    
try:
    import json
except ImportError:
    import simplejson as json

AMI_RECONNECT_INTERVAL      = 10
TASK_CHECK_STATUS_INTERVAL  = 10



class ServerObject(BasicObject):
    _maxConcurrentTasks = 1
    _runningTasks       = 0
    _queuedTasks        = []
    
    _callid = 0
    _calls  = {}
    
    def __init__(self):
        BasicObject.__init__(self, "Server")
    
    def _getTaskId(self):
        self._callid += 1
        return self._callid
    
    def pushTask(self, task, *args, **kwargs):
        if self._runningTasks < self._maxConcurrentTasks:
            self._runningTasks += 1
            taskid              = self._getTaskId()
            taskdf              = task(*args, **kwargs).addBoth(self._onTaskDone, taskid)
            calltm              = reactor.callLater(5, self._fireTimeout, taskid, taskdf)
            self._calls[taskid] = calltm
            return taskdf
        queuedf = defer.Deferred()
        self._queuedTasks.append((task, args, kwargs, queuedf))
        return queuedf
    
    def _onTaskDone(self, taskdone, taskid):
        self._runningTasks -= 1
        ## Remove Call
        calltm = self._calls.get(taskid)
        if calltm:
            del self._calls[taskid]
            calltm.cancel()
        ## Call next task if exists
        if self._runningTasks < self._maxConcurrentTasks and self._queuedTasks:
            self._runningTasks         += 1
            task, args, kwargs, queuedf = self._queuedTasks.pop(0)
            taskid                      = self._getTaskId()
            taskdf                      = task(*args, **kwargs).addBoth(self._onTaskDone, taskid)
            taskdf.chainDeferred(queuedf)
            calltm                      = reactor.callLater(5, self._fireTimeout, taskid, taskdf)
            self._calls[taskid]         = calltm
        ## Raize Feilure
        if isinstance(taskdone, failure.Failure):
            taskdone.trap()
        return taskdone
    
    def _fireTimeout(self, taskid, taskdf):
        ## Remove Call
        calltm = self._calls.get(taskid)
        if calltm:
            del self._calls[taskid]
        ## Fire Timeout
        if not taskdf.called:
            defer.timeout(taskdf)
            
    def clearCalls(self):
        ## Clear Pending Calls
        for taskid, call in self._calls.items():
            if call:
                call.args[1].errback(failure.Failure(AMICommandFailure("Connection closed")))
        self._calls.clear()
        ## Clear Queue
        while self._queuedTasks:
            task, args, kwargs, queuedf = self._queuedTasks.pop(0)
            queuedf.errback(failure.Failure(AMICommandFailure("Connection closed")))


class OdinAMIProtocol(manager.AMIProtocol):
    """docstring for OdinAMIProtocol"""
    def connectionLost(self, reason):
        """Connection lost, clean up callbacks"""
        for key,callable in self.actionIDCallbacks.items():
            try:
                callable(tw_error.ConnectionDone("""AMI connection terminated"""))
            except Exception, err:
                logger.error("""Failure during connectionLost for callable %s: %s""", callable, err)
        self.actionIDCallbacks.clear()
        self.eventTypeCallbacks.clear()
        
    def collectDeferred(self, message, stopEvent):
        """Collect all responses to this message until stopEvent or error
           returns deferred returning sequence of events/responses
        """
        df = defer.Deferred()
        cache = []
        def onEvent(event):
            if type(event) == type(dict()):
                if event.get('response') == 'Error':
                    df.errback(AMICommandFailure(event))
                elif event['event'] == stopEvent:
                    df.callback(cache)
                else:
                    cache.append(event)
            else:
                df.errback(AMICommandFailure(event))
        actionid = self.sendMessage(message, onEvent)
        df.addCallbacks(
            self.cleanup, self.cleanup,
            callbackArgs=(actionid,), errbackArgs=(actionid,)
        )
        return df
    
    def errorUnlessResponse(self, message, expected='Success'):
        """Raise a AMICommandFailure error unless message['response'] == expected
        If == expected, returns the message
        """
        if type(message) == type(dict()) and message['response'] != expected or type(message) != type(dict()):
            raise AMICommandFailure(message)
        return message
    
    def redirect(self, channel, context, exten, priority, extraChannel = None, extraContext = None, extraExten = None, extraPriority = None):
        """Transfer channel(s) to given context/exten/priority"""
        message = {
            'action': 'redirect', 'channel': channel, 'context': context,
            'exten': exten, 'priority': priority,
        }
        if extraChannel is not None:
            message['extrachannel'] = extraChannel
        if extraExten is not None:
            message['extraexten'] = extraExten
        if extraContext is not None:
            message['extracontext'] = extraContext
        if extraPriority is not None:
            message['extrapriority'] = extraPriority
        return self.sendDeferred(message).addCallback(self.errorUnlessResponse)

    def stopMonitor(self, channel):
        """Stop monitoring the given channel"""
        message = {"action": "stopmonitor", "channel": channel}
        return self.sendDeferred(message).addCallback(self.errorUnlessResponse)

    def queueAdd(self, queue, interface, penalty=0, paused=True, membername=None, stateinterface=None):
        """Add given interface to named queue"""
        if paused in (True,'true',1):
            paused = 'true'
        else:
            paused = 'false'
        message = {'action': 'queueadd', 'queue': queue, 'interface': interface, 'penalty':penalty, 'paused': paused}
        if membername is not None:
            message['membername'] = membername
        if stateinterface is not None:
            message['stateinterface'] = stateinterface
        return self.sendDeferred(message).addCallback(self.errorUnlessResponse)

        

class OdinAMIFactory(manager.AMIFactory):
    amiWorker  = None
    servername = None
    protocol   = OdinAMIProtocol
    """docstring for ClassName"""
    def __init__(self, servername, username, password, amiWorker):
        self.servername = servername
        self.amiWorker  = amiWorker
        manager.AMIFactory.__init__(self, username, password)

    def clientConnectionLost(self, connector, reason):
        logger.warning("Server %s :: Lost connection to AMI: %s" % (self.servername, reason.value))
        self.amiWorker.__disconnected__(self.servername)
        reactor.callLater(AMI_RECONNECT_INTERVAL, self.amiWorker.connect, self.servername)

    def clientConnectionFailed(self, connector, reason):
        logger.error("Server %s :: Failed to connected to AMI: %s" % (self.servername, reason.value))
        self.amiWorker.__disconnected__(self.servername)
        reactor.callLater(AMI_RECONNECT_INTERVAL, self.amiWorker.connect, self.servername)

    def disconnect(self):
        #TODO : I must or not :-) find a clean solution for disconenct from the asterisk server
        logger.error("Server %s :: I'm disconnecting..." % (self.servername))
        
class OdinAMIFacade(object):
    """docstring for OdinAMIFacade"""
    servers            = {}

    def __init__(self, config, redisPublisher):
        super(OdinAMIFacade, self).__init__()
        ## Initialize logger
        global logger
        self._redisPublisher = redisPublisher
        logger.debug('amifacade ctor')
        self.eventHandlers = {
            'Reload'              : self.handler_event_reload,
            'PeerEntry'           : self.handler_event_peer_entry,
            'PeerStatus'          : self.handler_event_peer_status,
            'Newchannel'          : self.handler_event_newchannel,
            'Newstate'            : self.handler_event_newstate,
            'Rename'              : self.handler_event_rename,
            #'Masquerade'          : self.handlerEventMasquerade,
            'NewCallerid'         : self.handler_event_newcallerid,
            'Hangup'              : self.handler_event_hangup,
            'Dial'                : self.handler_event_dial,
            'Link'                : self.handler_event_link,
            'Unlink'              : self.handler_event_unlink,
            'Bridge'              : self.handler_event_bridge,
            'ParkedCall'          : self.handler_event_parked_call,
            'UnParkedCall'        : self.handler_event_unparked_call,
            'ParkedCallTimeOut'   : self.handler_event_parked_call_timeout,
            'ParkedCallGiveUp'    : self.handler_event_parked_call_giveup,
            'Alarm'               : self.handler_event_alarm,
            'AlarmClear'          : self.handler_event_alarm_clear,
            'UserEvent'           : self.handler_event_user,
            'MonitorStart'        : self.handler_event_monitor_start,
            'MonitorStop'         : self.handler_event_monitor_stop

        }

        self.requestHandlers = {
            'get_servers'           : self.request_handler_get_servers,
            'get_server_status'     : self.request_handler_get_server_status,
            'originate'             : self.request_handler_originate,
            'request_info'          : self.request_handler_request_info,
            'hangupchannel'         : self.request_handler_hangupchannel,
            'get_active_calls'      : self.request_handler_get_active_calls,
            'parkchannel'           : self.request_handler_parkchannel,
            'transfer'              : self.request_handler_transfer,
            'start_monitor'         : self.request_handler_start_monitor,
            'stop_monitor'          : self.request_handler_stop_monitor,
            'chan_spy'              : self.request_handler_chan_spy,

        }

        self.actionHandlers = {
            'cli_command'         : ('command', self.client_action_cli_command)
        }

        ## Reading servers sections
        servers = [s for s in config.sections() if s.startswith('server:')]
        servers.sort()
        #
        for server in servers:
            servername = server.replace('server:', '').strip()
            username   = config.get(server, 'username')
            password   = config.get(server, 'password')
            
            self.servers[servername]                  = ServerObject()
            self.servers[servername].servername       = servername
            self.servers[servername].version          = None
            self.servers[servername].lastReload       = 0
            self.servers[servername].hostname         = config.get(server, 'hostname')
            self.servers[servername].hostport         = int(config.get(server, 'hostport'))
            self.servers[servername].username         = config.get(server, 'username')
            self.servers[servername].password         = config.get(server, 'password')
            self.servers[servername].default_context  = config.get(server, 'default_context')
            self.servers[servername].transfer_context = config.get(server, 'transfer_context')
            #self.servers[servername].meetme_context   = config.get(server, 'meetme_context')
            #self.servers[servername].meetme_prefix    = config.get(server, 'meetme_prefix')
            
            self.servers[servername].connected        = False
            self.servers[servername].factory          = OdinAMIFactory(servername, username, password, self)
            self.servers[servername].ami              = None
            self.servers[servername].taskCheckStatus  = task.LoopingCall(self.taskCheckStatus, servername)
            
            self.servers[servername].status              = BasicObject()
            #self.servers[servername].status.meetmes      = {}
            self.servers[servername].status.channels     = {}
            self.servers[servername].status.bridges      = {}
            self.servers[servername].status.peers        = {
                'SIP': {},
                'IAX2': {},
                'DAHDI': {},
                'Khomp': {},
            }
            self.servers[servername].peergroups          = {}
            self.servers[servername].displayUsers        = {}
            #self.servers[servername].displayMeetmes      = {}
            self.servers[servername].displayQueues       = {}
            self.servers[servername].status.queues       = {}
            self.servers[servername].status.queueMembers = {}
            self.servers[servername].status.queueClients = {}
            self.servers[servername].status.queueCalls   = {}
            self.servers[servername].status.parkedCalls  = {}
            
            self.servers[servername].queueMapName        = {}
            self.servers[servername].queueMapMember      = {}
        #
        ## Peers Groups
        for peergroup, peers in config.items('peers'):
            if peergroup in ('default', 'sortby'):
                continue
            if re.match("^[^\/]+\/@group\/[^\/]+", peergroup):
                servername, peergroup = peergroup.replace('@group/', '').split('/', 1)
                server = self.servers.get(servername)
                if server:
                    peergroup = peergroup.strip()
                    peers     = peers.split(',')
                    for peer in peers:
                        tech, peer = peer.split('/', 1)
                        tech = tech.strip()
                        peer = peer.strip()
                        if not server.peergroups.has_key(tech):
                            server.peergroups[tech] = {}
                        server.peergroups[tech][peer] = peergroup

        ## Peers
        self.displayUsersDefault = config.get('peers', 'default') == 'show'
        try:
            self.sortPeersBy = config.get('peers', 'sortby')
            if not self.sortPeersBy in ('channel', 'callerid'):
                logger.error("Invalid value for 'sortby' in section 'peers' of config file. valid options: channel, callerid")
                self.sortPeersBy = 'callerid'
        except NoOptionError:
            self.sortPeersBy = 'callerid'
            logger.error("No option 'sortby' in section: 'peers' of config file, sorting by CallerID")

        for user, display in config.items('peers'):
            if user in ('default', 'sortby'):
                continue
            
            if not re.match("^[^\/]+\/[^\/@]+\/[^\/]+", user):
                continue
            
            servername, user = user.split('/', 1)
            server = self.servers.get(servername)
            if not server:
                continue
            
            tech, peer = user.split('/')
            
            if tech in server.status.peers.keys(): 
                if (self.displayUsersDefault and display == 'hide') or (not self.displayUsersDefault and display == 'show'):
                    server.displayUsers[user] = True
                    
            if display.startswith('force'):
                tmp       = display.split(',')
                display   = tmp[0].strip()
                status    = '--'
                callerid  = '--'
                forcedCid = False
                if len(tmp) == 2:
                    callerid  = tmp[1].strip()
                    forcedCid = True
                
                self._createPeer(
                    servername, 
                    channeltype = tech, 
                    peername    = peer,
                    callerid    = callerid,
                    status      = status,
                    forced      = True,
                    forcedCid   = forcedCid,
                    _log        = '(forced peer)'
                )

        #for servers
        self.__start()

        
    
    def __start(self):
        logger.info("Starting Odin Asterisk Services...")
        for servername in self.servers:
            reactor.callWhenRunning(self.connect, servername)

    def stop(self):
        for servername in self.servers:
            server = self.servers.get(servername)
            if server.connected:
                server.factory.disconnect()
    
    def __connected__(self, ami, servername):
        logger.info("Server %s :: Marking as connected..." % servername)
        ami.servername   = servername
        server           = self.servers.get(servername)
        server.connected = True
        server.ami       = ami
        
        ## Request Server Version
        def _onCoreShowVersion(result):
            versions = [1.4, 1.6, 1.8]
            logger.info("Server %s :: %s" %(servername, result[0]))
            for version in versions:
                if "Asterisk %s" % version in result[0]:
                    server.version = version
                    break
            for event, handler in self.eventHandlers.items():
                logger.debug("Server %s :: Registering EventHandler for %s" % (servername, event))
                server.ami.registerEvent(event, handler)
            logger.debug("Server %s :: Starting Task Check Status..." % servername)
            server.taskCheckStatus.start(TASK_CHECK_STATUS_INTERVAL, False)
            self._requestAsteriskConfig(servername)
            
        server.pushTask(server.ami.command, 'core show version') \
            .addCallbacks(_onCoreShowVersion, self._onAmiCommandFailure, errbackArgs = (servername, "Error Requesting Asterisk Version"))
        
    def __disconnected__(self, servername):
        server = self.servers.get(servername)
        if server.connected:
            logger.info("Server %s :: Marking as disconnected..." % servername)
            logger.debug("Server %s :: Stopping Task Check Status..." % servername)
            server.clearCalls()
            if server.taskCheckStatus.running:
                server.taskCheckStatus.stop()
        server.connected = False
        server.ami       = None
    
    def connect(self, servername):
        server = self.servers.get(servername)
        logger.info("Server %s :: Trying to connect to AMI at %s:%d" % (servername, server.hostname, server.hostport))
        df = server.factory.login(server.hostname, server.hostport)
        df.addCallback(self.onLoginSuccess, servername)
        df.addErrback(self.onLoginFailure, servername)
        return df
    
    def onLoginSuccess(self, ami, servername):
        logger.info("Server %s :: AMI Connected..." % (servername))
        self.__connected__(ami, servername)
        
    def onLoginFailure(self, reason, servername):
        logger.error("Server %s :: Odin Asterisk facade AMI Failed to Login, reason: %s" % (servername, reason.getErrorMessage()))
        self.__disconnected__(servername)
    ## transport helper functions
    def __publishMessage(self, servername, id, objname, obj):
        to_json = {"id": id, "server": servername, objname: obj}
        message = json.dumps(to_json, cls=BasicObjectEncoder)
        #logger.debug("Server %s :: Publishe message to the redis : %s" % (servername, message))
        self._redisPublisher.publish("odin_ami_data_channel", message)

    ##worker functions
    ## Channels 
    def _createChannel(self, servername, **kw):
        server        = self.servers.get(servername)
        uniqueid      = kw.get('uniqueid')
        channel       = kw.get('channel')
        _log          = kw.get('_log', '')
        
        if not server.status.channels.has_key(uniqueid):
            chan              = BasicObject("Channel")
            chan.uniqueid     = uniqueid
            chan.channel      = channel
            chan.state        = kw.get('state', 'Unknown')
            chan.calleridnum  = kw.get('calleridnum', '')
            chan.calleridname = kw.get('calleridname', '')
            chan.monitor      = kw.get('monitor', False)
            chan.spy          = kw.get('spy', False)
            chan.starttime    = time.time()
            
            logger.debug("Server %s :: Channel create: %s (%s) %s", servername, uniqueid, channel, _log)
            server.status.channels[uniqueid] = chan
            #notify http clients
            self.__publishMessage(servername, "createchannel", "channel", chan)
            #
            channeltype, peername = channel.rsplit('-', 1)[0].split('/', 1)
            self._updatePeer(servername, channeltype = channeltype, peername = peername, _action = 'increaseCallCounter')
            #
            if logging.DUMPOBJECTS:
                logger.debug("Object Dump:%s", chan)
            return True
        else:
            if not kw.get('_isCheckStatus'):
                logger.warning("Server %s :: Channel already exists: %s (%s)", servername, uniqueid, channel)
        return False
    
    def _lookupChannel(self, servername, chan):
        server  = self.servers.get(servername)
        channel = None
        for uniqueid, channel in server.status.channels.items():
            if channel.channel == chan:
                break
        return channel
    
    def _updateChannel(self, servername, **kw):
        uniqueid = kw.get('uniqueid')
        channel  = kw.get('channel')
        _log     = kw.get('_log', '')
        
        try:
            chan = self.servers.get(servername).status.channels.get(uniqueid)
            if chan:
                logger.debug("Server %s :: Channel update: %s (%s) %s", servername, uniqueid, chan.channel, _log)
                for k, v in kw.items():
                    if k not in ('_log'):
                        if chan.__dict__.has_key(k):
                            chan.__dict__[k] = v
                        else:
                            logger.warning("Server %s :: Channel %s (%s) does not have attribute %s", servername, uniqueid, chan.channel, k)
                #notify clients
                ##self.http._addUpdate(servername = servername, subaction = 'Update', **chan.__dict__.copy())
                #notify http clients
                self.__publishMessage(servername, "updatechannel", "channel", chan)
                #to_json=[]
                #to_json.append({"id": "ami:updatechannel", "server": servername, "channel" : chan})
                #self._redisPublisher.publish("odin_ami_data_channel", json.dumps(to_json, cls=BasicObjectEncoder))
                #
                if logging.DUMPOBJECTS:
                    logger.debug("Object Dump:%s", chan)
            else:
                logger.warning("Server %s :: Channel not found: %s (%s) %s", servername, uniqueid, channel, _log)
        except:
            logger.exception("Server %s :: Unhandled exception updating channel: %s (%s)", servername, uniqueid, channel)
            
    def _removeChannel(self, servername, **kw):
        uniqueid = kw.get('uniqueid')
        channel  = kw.get('channel')
        _log     = kw.get('_log', '')
        try:
            server = self.servers.get(servername)
            chan   = server.status.channels.get(uniqueid)
            if chan:
                logger.debug("Server %s :: Channel remove: %s (%s) %s", servername, uniqueid, chan.channel, _log)
                if kw.get('_isLostChannel'):
                    logger.warning("Server %s :: Removing lost channel: %s (%s)", servername, uniqueid, chan.channel)
                else:
                    bridgekey = self._locateBridge(servername, uniqueid = uniqueid)
                    if bridgekey:
                        self._removeBridge(servername, uniqueid = bridgekey[0], bridgeduniqueid = bridgekey[1], _log = _log)
                del server.status.channels[uniqueid]
                #
                self.__publishMessage(servername, "removechannel", "channel", chan)
                
                channeltype, peername = channel.rsplit('-', 1)[0].split('/', 1)
                self._updatePeer(servername, channeltype = channeltype, peername = peername, _action = 'decreaseCallCounter')
                
                if logging.DUMPOBJECTS:
                    logger.debug("Object Dump:%s", chan)
            else:
                logger.warning("Server %s :: Channel does not exists: %s (%s)", servername, uniqueid, channel)
        except:
            logger.exception("Server %s :: Unhandled exception removing channel: %s (%s)", servername, uniqueid, channel)
    
    ## Bridges
    def _createBridge(self, servername, **kw):
        server          = self.servers.get(servername)
        uniqueid        = kw.get('uniqueid')
        channel         = kw.get('channel')
        bridgeduniqueid = kw.get('bridgeduniqueid')
        bridgedchannel  = kw.get('bridgedchannel')
        bridgekey       = (uniqueid, bridgeduniqueid) 
        _log            = kw.get('_log', '')
        
        if not server.status.bridges.has_key(bridgekey):
            if not server.status.channels.has_key(uniqueid):
                logger.warning("Server %s :: Could not create bridge %s (%s) with %s (%s). Source Channel not found.", servername, uniqueid, channel, bridgeduniqueid, bridgedchannel)
                return False
            if not server.status.channels.has_key(bridgeduniqueid):
                logger.warning("Server %s :: Could not create bridge %s (%s) with %s (%s). Bridged Channel not found.", servername, uniqueid, channel, bridgeduniqueid, bridgedchannel)
                return False
                
            bridge                 = BasicObject("Bridge")
            bridge.uniqueid        = uniqueid
            bridge.bridgeduniqueid = bridgeduniqueid
            bridge.channel         = channel
            bridge.bridgedchannel  = bridgedchannel
            bridge.status          = kw.get('status', 'Link')
            bridge.dialtime        = kw.get('dialtime', time.time())
            bridge.linktime        = kw.get('linktime', 0)
            bridge.seconds         = int(time.time() - bridge.linktime)
            
            logger.debug("Server %s :: Bridge create: %s (%s) with %s (%s) %s", servername, uniqueid, channel, bridgeduniqueid, bridgedchannel, _log)
            server.status.bridges[bridgekey] = bridge
            self.__publishMessage(servername, "createbridge", "bridge", bridge)
            if logging.DUMPOBJECTS:
                logger.debug("Object Dump:%s", bridge)
            return True
        else:
            logger.warning("Server %s :: Bridge already exists: %s (%s) with %s (%s)", servername, uniqueid, channel, bridgeduniqueid, bridgedchannel)
        return False
    
    def _updateBridge(self, servername, **kw):
        uniqueid        = kw.get('uniqueid')
        channel         = kw.get('channel')
        bridgeduniqueid = kw.get('bridgeduniqueid')
        bridgedchannel  = kw.get('bridgedchannel')
        _log            = kw.get('_log', '')
        try:
            bridge = kw.get('_bridge', self.servers.get(servername).status.bridges.get((uniqueid, bridgeduniqueid)))
            if bridge:
                logger.debug("Server %s :: Bridge update: %s (%s) with %s (%s) %s", servername, bridge.uniqueid, bridge.channel, bridge.bridgeduniqueid, bridge.bridgedchannel, _log)
                for k, v in kw.items():
                    if k not in ('_log', '_bridge'):
                        if bridge.__dict__.has_key(k):
                            bridge.__dict__[k] = v
                        else:
                            logger.warning("Server %s :: Bridge %s (%s) with %s (%s) does not have attribute %s", servername, uniqueid, bridge.channel, bridgeduniqueid, bridge.bridgedchannel, k)
                bridge.seconds = int(time.time() - bridge.linktime)
                self.__publishMessage(servername, "updatebridge", "bridge", bridge)
                if logging.DUMPOBJECTS:
                    logger.debug("Object Dump:%s", bridge)
            else:
                logger.warning("Server %s :: Bridge not found: %s (%s) with %s (%s)", servername, uniqueid, channel, bridgeduniqueid, bridgedchannel)
        except:
            logger.exception("Server %s :: Unhandled exception updating bridge: %s (%s) with %s (%s)", servername, uniqueid, channel, bridgeduniqueid, bridgedchannel)
    
    def _locateBridge(self, servername, **kw):
        server          = self.servers.get(servername)
        uniqueid        = kw.get('uniqueid')
        bridgeduniqueid = kw.get('bridgeduniqueid')
        
        if uniqueid and bridgeduniqueid:
            return [None, (uniqueid, bridgeduniqueid)][server.status.bridges.has_key((uniqueid, bridgeduniqueid))]
        
        bridges = [i for i in server.status.bridges.keys() if uniqueid in i or bridgeduniqueid in i]
        if len(bridges) == 1:
            return bridges[0]
        if len(bridges) > 1:
            logger.warning("Server %s :: Found more than one bridge with same uniqueid: %s", servername, bridges)
            return None
    
    def _removeBridge(self, servername, **kw):
        uniqueid        = kw.get('uniqueid')
        channel         = kw.get('channel')
        bridgeduniqueid = kw.get('bridgeduniqueid')
        bridgedchannel  = kw.get('bridgedchannel')
        bridgekey       = (uniqueid, bridgeduniqueid)
        _log            = kw.get('_log', '')
        try:
            server = self.servers.get(servername)
            bridge = server.status.bridges.get(bridgekey)
            if bridge:
                logger.debug("Server %s :: Bridge remove: %s (%s) with %s (%s) %s", servername, uniqueid, bridge.channel, bridge.bridgeduniqueid, bridge.bridgedchannel, _log)
                if kw.get('_isLostBridge'):
                    logger.warning("Server %s :: Removing lost bridge: %s (%s) with %s (%s)", servername, uniqueid, bridge.channel, bridge.bridgeduniqueid, bridge.bridgedchannel)
                del server.status.bridges[bridgekey]
                self.__publishMessage(servername, "removebridge", "bridge", bridge)
                #self.http._addUpdate(servername = servername, action = 'RemoveBridge', uniqueid = uniqueid, bridgeduniqueid = bridgeduniqueid)
                if logging.DUMPOBJECTS:
                    logger.debug("Object Dump:%s", bridge)
            else:
                logger.warning("Server %s :: Bridge does not exists: %s (%s) with %s (%s)", servername, uniqueid, channel, bridgeduniqueid, bridgedchannel)
        except:
            logger.exception("Server %s :: Unhandled exception removing bridge: %s (%s) with %s (%s)", servername, uniqueid, channel, bridgeduniqueid, bridgedchannel)

    ##
    ## Event Handlers
    ##
    def handler_event_reload(self, ami, event):
        logger.debug("Server %s :: Processing Event Reload..." % ami.servername)        
        server = self.servers.get(ami.servername)
        if time.time() - server.lastReload > 5:
            server.lastReload = time.time()
            self._requestAsteriskConfig(ami.servername)

    def handler_event_peer_entry(self, ami, event):
        logger.debug("Server %s :: Processing Event PeerEntry 1 ..." % ami.servername)
        server      = self.servers.get(ami.servername)
        status      = event.get('status')
        channeltype = event.get('channeltype')
        objectname  = event.get('objectname').split('/')[0]
        time        = -1
        reTime = re.compile("([0-9]+)\s+ms")
        gTime  = reTime.search(status)
        if gTime:
            time = int(gTime.group(1))
        
        if status.startswith('OK'):
            status = 'Registered'
        elif status.find('(') != -1:
            status = status[0:status.find('(')]
            
        user = '%s/%s' % (channeltype, objectname)
        if (self.displayUsersDefault and not server.displayUsers.has_key(user)) or (not self.displayUsersDefault and server.displayUsers.has_key(user)):
            self._createPeer(
                ami.servername,
                channeltype = channeltype,
                peername    = objectname,
                status      = status,
                time        = time
            )
        else:
            user = None
        #
        if user:
            type    = ['peer', 'user'][channeltype == 'Skype']
            command = '%s show %s %s' % (channeltype.lower(), type, objectname)
            
            def onShowPeer(response):
                logger.debug("Server %s :: Processing %s..." % (ami.servername, command))
                result    = '\n'.join(response)
                callerid  = None
                context   = None
                variables = []
                
                try:
                    callerid = re.compile("['\"]").sub("", re.search('Callerid[\s]+:[\s](.*)\n', result).group(1))
                    if callerid == ' <>':
                        callerid = '--'
                except:
                    callerid = '--'
                
                try:
                    context = re.search('Context[\s]+:[\s](.*)\n', result).group(1)
                except:
                    context = server.default_context
                
                start = False
                for line in response:
                    if re.search('Variables[\s+]', line):
                        start = True
                        continue
                    if start:
                        gVar = re.search('^[\s]+([^=]*)=(.*)', line)
                        if gVar:
                            variables.append("%s=%s" % (gVar.group(1).strip(), gVar.group(2).strip()))
                
                self._updatePeer(
                    ami.servername, 
                    channeltype = channeltype, 
                    peername    = objectname,
                    callerid    = [callerid, objectname][callerid == "--"],
                    context     = context,
                    variables   = variables
                )
                    
            server.pushTask(server.ami.command, command) \
                .addCallbacks(onShowPeer, self._onAmiCommandFailure, \
                    errbackArgs = (ami.servername, "Error Executting Command '%s'" % command))
    #
    def handler_event_peer_status(self, ami, event):
        logger.debug("Server %s :: Processing Event PeerStatus..." % ami.servername)
        channel = event.get('peer')
        status  = event.get('peerstatus')
        time    = event.get('time')
        channeltype, peername = channel.split('/', 1)
        
        if time:
            self._updatePeer(ami.servername, channeltype = channeltype, peername = peername, status = status, time = time)
        else:
            self._updatePeer(ami.servername, channeltype = channeltype, peername = peername, status = status)

    def handler_event_newchannel(self, ami, event):
        logger.debug("Server %s :: Processing Event Newchannel..." % ami.servername)
        server   = self.servers.get(ami.servername)
        uniqueid = event.get('uniqueid')
        channel  = event.get('channel')
        
        self._createChannel(
            ami.servername,
            uniqueid     = uniqueid,
            channel      = channel,
            state        = event.get('channelstatedesc', event.get('state')),
            calleridnum  = event.get('calleridnum'),
            calleridname = event.get('calleridname'),
            _log         = "-- Newchannel"
        )
        
    def handler_event_newstate(self, ami, event):
        logger.debug("Server %s :: Processing Event Newstate..." % ami.servername)
        server       = self.servers.get(ami.servername)     
        uniqueid     = event.get('uniqueid')
        channel      = event.get('channel')
        state        = event.get('channelstatedesc', event.get('state'))
        calleridnum  = event.get('calleridnum', event.get('callerid'))
        calleridname = event.get('calleridname')
        
        self._updateChannel(
            ami.servername,
            uniqueid     = uniqueid,
            channel      = channel,
            state        = state,
            calleridnum  = calleridnum,
            calleridname = calleridname,
            _log         = "-- State changed to %s" % state
        )

    def handler_event_rename(self, ami, event):
        logger.debug("Server %s :: Processing Event Rename..." % ami.servername)
        uniqueid = event.get('uniqueid')
        channel  = event.get('channel')
        newname  = event.get('newname')
        
        self._updateChannel(ami.servername, uniqueid = uniqueid, channel = newname, _log = "Channel %s renamed to %s" % (channel, newname))
        bridgekey = self._locateBridge(ami.servername, uniqueid = uniqueid)
        if bridgekey:
            if uniqueid == bridgekey[0]:
                self._updateBridge(ami.servername, uniqueid = bridgekey[0], bridgeduniqueid = bridgekey[1], channel = newname, _log = "Channel %s renamed to %s" % (channel, newname))
            else:
                self._updateBridge(ami.servername, uniqueid = bridgekey[0], bridgeduniqueid = bridgekey[1], bridgedchannel = newname, _log = "Channel %s renamed to %s" % (channel, newname))


    def handler_event_newcallerid(self,ami, event):
        logger.debug("Server %s :: Processing Event Newcallerid..." % ami.servername)
        server       = self.servers.get(ami.servername) 
        uniqueid     = event.get('uniqueid')
        channel      = event.get('channel')
        calleridnum  = event.get('calleridnum', event.get('callerid'))
        calleridname = event.get('calleridname')
        
        self._updateChannel(
            ami.servername,
            uniqueid     = uniqueid,
            channel      = channel,
            calleridnum  = calleridnum,
            calleridname = calleridname,
            _log         = "-- Callerid updated to '%s <%s>'" % (calleridname, calleridnum)
        )
        bridgekey = self._locateBridge(ami.servername, uniqueid = uniqueid)
        if bridgekey:
            self._updateBridge(ami.servername, uniqueid = bridgekey[0], bridgeduniqueid = bridgekey[1], _log = "-- Touching Bridge...")

    def handler_event_link(self, ami, event):
        logger.debug("Server %s :: Processing Event Link..." % ami.servername)
        server          = self.servers.get(ami.servername)
        uniqueid        = event.get('uniqueid1')
        channel         = event.get('channel1')
        bridgeduniqueid = event.get('uniqueid2')
        bridgedchannel  = event.get('channel2')
        callerid        = event.get('callerid1')
        bridgedcallerid = event.get('callerid2')
        
        bridgekey = self._locateBridge(ami.servername, uniqueid = uniqueid, bridgeduniqueid = bridgeduniqueid)
        if bridgekey:
            linktime = server.status.bridges.get(bridgekey).linktime
            self._updateBridge(
                ami.servername,
                uniqueid        = uniqueid, 
                bridgeduniqueid = bridgeduniqueid,
                status          = 'Link',
                linktime        = [linktime, time.time()][linktime == 0],
                _log            = "-- Status changed to Link"
            )
        else:
            self._createBridge(
                ami.servername,
                uniqueid        = uniqueid, 
                bridgeduniqueid = bridgeduniqueid,
                channel         = channel,
                bridgedchannel  = bridgedchannel,
                status          = 'Link',
                linktime        = time.time(),
                _log            = "-- Link"
            )
        
        # TODO Detect QueueCall

    def handler_event_unlink(self, ami, event):
        logger.debug("Server %s :: Processing Event Unlink..." % ami.servername)
        server          = self.servers.get(ami.servername)
        uniqueid        = event.get('uniqueid1')
        channel         = event.get('channel1')
        bridgeduniqueid = event.get('uniqueid2')
        bridgedchannel  = event.get('channel2')
        self._updateBridge(
            ami.servername, 
            uniqueid        = uniqueid, 
            bridgeduniqueid = bridgeduniqueid,
            channel         = channel,
            bridgedchannel  = bridgedchannel,
            status          = 'Unlink',
            _log            = "-- Status changed to Unlink"
        )
        
        # Detect QueueCall

    def handler_event_bridge(self, ami, event):
        logger.debug("Server %s :: Processing Event Bridge..." % ami.servername)
        self.handler_event_link(ami, event)
    
    def handler_event_hangup(self, ami, event):
        logger.debug("Server %s :: Processing Event Hangup..." % ami.servername)
        server   = self.servers.get(ami.servername)
        uniqueid = event.get('uniqueid')
        channel  = event.get('channel')
        
        self._removeChannel(
            ami.servername,
            uniqueid = uniqueid,
            channel  = channel,
            _log     = "-- Hangup"
        )
        
        # Detect QueueCall
        """queueCall = server.status.queueCalls.get(uniqueid)
        if queueCall:
            log.debug("Server %s :: Queue update, call hangup: %s -> %s", ami.servername, queueCall.client.get('queue'), uniqueid)
            del server.status.queueCalls[uniqueid]
            if queueCall.member:
                self.http._addUpdate(servername = ami.servername, action = "RemoveQueueCall", uniqueid = uniqueid, queue = queueCall.client.get('queue'), location = queueCall.member.get('location'))
                queue = server.status.queues.get(queueCall.client.get('queue'))
                queue.completed += 1
                self.http._addUpdate(servername = ami.servername, subaction = 'Update', **queue.__dict__.copy())
            if logging.DUMPOBJECTS:
                log.debug("Object Dump:%s", queueCall)
        # Detect QueueClient
        for qname, clientuniqueid in server.status.queueClients.items():
            if clientuniqueid == uniqueid:
                self._updateQueue(ami.servername, queue = qname, event = "Leave", uniqueid = uniqueid, _log = "By Channel Hangup")  
        """

    def handler_event_dial(self, ami, event):
        logger.debug("Server %s :: Processing Event Dial..." % ami.servername)
        server   = self.servers.get(ami.servername)
        subevent = event.get('subevent', "begin")
        if subevent.lower() == 'begin':
            logger.debug("Server %s :: Processing Event Dial -> SubEvent Begin..." % ami.servername)
            self._createBridge(
                ami.servername,
                uniqueid        = event.get('uniqueid', event.get('srcuniqueid')),
                channel         = event.get('channel', event.get('source')),
                bridgeduniqueid = event.get('destuniqueid'),
                bridgedchannel  = event.get('destination'),
                status          = 'Dial',
                dialtime        = time.time(),
                _log            = '-- Dial Begin'
            )
        elif subevent.lower() == 'end':
            logger.debug("Server %s :: Processing Event Dial -> SubEvent End..." % ami.servername)
            bridgekey = self._locateBridge(ami.servername, uniqueid = event.get('uniqueid'))
            if bridgekey:
                self._removeBridge(ami.servername, uniqueid = bridgekey[0], bridgeduniqueid = bridgekey[1], _log = "-- Dial End")
                
            # TODO Detect QueueCall

        else:
            logger.warning("Server %s :: Unhandled Dial SubEvent %s", ami.servername, subevent)

    # Parked calls events
    def handler_event_parked_call(self, ami, event):
        logger.debug("Server %s :: Processing Event ParkedCall..." % ami.servername)
        self._createParkedCall(ami.servername, **event)
 
    def handler_event_unparked_call(self, ami, event):
        logger.debug("Server %s :: Processing Event UnParkedCall..." % ami.servername)
        self._removeParkedCall(ami.servername, **event)

    def handler_event_parked_call_timeout(self, ami, event):
        logger.debug("Server %s :: Processing Event ParkedCallTimeout..." % ami.servername)
        self._removeParkedCall(ami.servername, **event)

    def handler_event_parked_call_giveup(self, ami, event):
        logger.debug("Server %s :: Processing Event ParkedCallGiveUp..." % ami.servername)
        self._removeParkedCall(ami.servername, **event)

    def handler_event_alarm(self, ami, event):
        '''
        Example 
        Alarm... [{'privilege': 'system,all', 'alarm': 'Red Alarm', 'event': 'Alarm', 'channel': '4'}]
        '''
        alarm = {}
        alarm.privilege = event.get('privilege')
        alarm.alarm = event.get('alarm')
        alarm.event = event.get('event')
        alarm.channel = event.get('channel')
        logger.debug("Server %s :: Processing Event Alarm... [%s]" % (ami.servername, event))
        self.__publishMessage(servername, "alarm", "alarm", alarm)

    def handler_event_alarm_clear(self, ami, event):
        '''
        Example
        AlarmClear...[{'privilege': 'system,all', 'event': 'AlarmClear', 'channel': '4'}]
        '''
        alarm = {}
        alarm.privilege = event.get('privilege')
        alarm.alarm = event.get('alarm')
        alarm.event = event.get('event')
        alarm.channel = event.get('channel')
        logger.debug("Server %s :: Processing Event AlarmClear...[%s]" % (ami.servername, event))
        self.__publishMessage(servername, "alarmclear", "alarm", alarm)

    def handler_event_user(self, ami, event):
        '''
        Processing Event AlarmClear...[{'privilege': 'user,all', 'userevent': 'Incomming', 'uniqueid': '1372759809.211', 'event': 'UserEvent', 'context': 'from-trixbox-be'}]
        '''
        logger.debug("Server %s :: Processing Event UserEvent ...[%s]" % (ami.servername, event))
        userevent = BasicObject('UserEvent')
        userevent.type = event.get('userevent', '')
        userevent.extention = event.get('extention', '')
        userevent.uniqueid = event.get('uniqueid', '')
        userevent.context = event.get('context', '')
        userevent.calleridnum = event.get('calleridnum', '')
        userevent.calleridname = event.get('calleridname', '')
        userevent.channel = event.get('channel', '')
        #
        self.__publishMessage(ami.servername, "userevent", "event", userevent)
        '''userevent.context = event.get('context')
        userevent.extention = event.get('extention')
        userevent.calleridnum = event.get('calleridnum')
        userevent.calleridname = event.get('calleridname')'''

    def handler_event_monitor_start(self, ami, event):
        logger.debug("Server %s :: Processing Event StartMonitor " % ami.servername)
        uniqueid     = event.get('uniqueid')
        channel      = event.get('channel')
        #
        self._updateChannel(ami.servername, uniqueid = uniqueid, channel = channel, monitor = True, _log = "-- Monitor Started")

    def handler_event_monitor_stop(self, ami, event):
        logger.debug("Server %s :: Processing Event StopMonitor " % ami.servername)
        uniqueid     = event.get('uniqueid')
        channel      = event.get('channel')
        #
        self._updateChannel(ami.servername, uniqueid = uniqueid, channel = channel, monitor = False, _log = "-- Monitor Stopped")



    ## 
    ## Client request handler
    ##
    def process_request(self, data):
        request = json.loads(data)
        requestId = request['id']
        if id == None:
            logger.error("I cant' find request id, the request ignored.")
            return
        logger.info("I'm processing request : %s" % (requestId))
        handler = self.requestHandlers.get(requestId)
        if handler:
            reactor.callWhenRunning(handler, request)
        else:
            logger.error("I can't find the request handler %s" %(requestId))

    def request_handler_get_servers(self, request):
        serversKeys = self.servers.keys()
        serversKeys.sort()
        #prepare message to the clients
        to_json={
            "id": "serverslist",
            "username": request['user'],
            "servers" : serversKeys
        }
        message = json.dumps(to_json, cls=BasicObjectEncoder)
        self._redisPublisher.publish("odin_ami_data_channel", message)
        logger.debug("I send the list of servers to the user %s servers [ %s ]"%(request['user'], message))

    def request_handler_get_server_status(self, request):
        logger.info("request_handler_get_server_status")
        tmp        = {}
        servername = request['servername']
        server     = self.servers.get(servername)
        username   = request['user']

        tmp[servername] = {
            'peers': {},
            'channels': [],
            'bridges': [],
            #'meetmes': [],
            'queues': [],
            'queueMembers': [],
            'queueClients': [],
            'queueCalls': [],
            'parkedCalls': []
        }
        ## Peers
        peers = {}
        channels = []
        queues = {}
        for tech, peerlist in server.status.peers.items():
            #tmp[servername]['peers'][tech] = []
            peers[tech] = []
            for peername, peer in peerlist.items():
                #tmp[servername]['peers'][tech].append(peer.__dict__)
                peers[tech].append(peer.__dict__)
            #tmp[servername]['peers'][tech].sort(lambda x, y: cmp(x.get(self.sortPeersBy), y.get(self.sortPeersBy)))
            peers[tech].sort(lambda x, y: cmp(x.get(self.sortPeersBy), y.get(self.sortPeersBy)))
        ## Channels
        for uniqueid, channel in server.status.channels.items():
            #tmp[servername]['channels'].append(channel.__dict__)
            channels.append(channel.__dict__)
        #tmp[servername]['channels'].sort(lambda x, y: cmp(x.get('starttime'), y.get('starttime')))
        channels.sort(lambda x, y: cmp(x.get('starttime'), y.get('starttime')))
        ## Bridges
        for uniqueid, bridge in server.status.bridges.items():
            bridge.seconds = [0, int(time.time() - bridge.linktime)][bridge.status == "Link"]
            tmp[servername]['bridges'].append(bridge.__dict__)
        tmp[servername]['bridges'].sort(lambda x, y: cmp(x.get('seconds'), y.get('seconds')))
        tmp[servername]['bridges'].reverse()
        #tmp[servername]['bridges'].sort(lambda x, y: cmp(x.get('dialtime'), y.get('dialtime')))
        ## Meetmes
        #for meetmeroom, meetme in server.status.meetmes.items():
        #    tmp[servername]['meetmes'].append(meetme.__dict__)
        #tmp[servername]['meetmes'].sort(lambda x, y: cmp(x.get('meetme'), y.get('meetme')))
        ## Parked Calls
        for channel, parked in server.status.parkedCalls.items():
            tmp[servername]['parkedCalls'].append(parked.__dict__)
        tmp[servername]['parkedCalls'].sort(lambda x, y: cmp(x.get('exten'), y.get('exten')))
        ## Queues
        for queuename, queue in server.status.queues.items():
            tmp[servername]['queues'].append(queue.__dict__)
            #queues.append(queue.__dict__)
        tmp[servername]['queues'].sort(lambda x, y: cmp(x.get('queue'), y.get('queue')))
        #queues.sort(lambda x, y: cmp(x.get('queue'), y.get('queue')))
        for (queuename, membername), member in server.status.queueMembers.items():
            member.pausedur = int(time.time() - member.pausedat)
            tmp[servername]['queueMembers'].append(member.__dict__)
        tmp[servername]['queueMembers'].sort(lambda x, y: cmp(x.get('name'), y.get('name')))
        for (queuename, uniqueid), client in server.status.queueClients.items():
            client.seconds = int(time.time() - client.jointime)
            tmp[servername]['queueClients'].append(client.__dict__)
        tmp[servername]['queueClients'].sort(lambda x, y: cmp(x.get('seconds'), y.get('seconds')))
        tmp[servername]['queueClients'].reverse()
        for uniqueid, call in server.status.queueCalls.items():
            if call.client and call.member:
                call.seconds = int(time.time() - call.starttime)  
                tmp[servername]['queueCalls'].append(call.__dict__)

        #prepare message to the clients
        to_json={
            "id": "serverstatus",
            "username": request['user'],
            "server" : servername,
            "peers" : peers,
            "channels" : channels,
            "queues" : tmp[servername]['queues']
        }
        #
        message = json.dumps(to_json, cls=BasicObjectEncoder)
        self._redisPublisher.publish("odin_ami_data_channel", message)
        logger.info("I posted the serverstatus message %s to the user." % (username))   
                     
    def request_handler_originate(self, request):
        ''' Process originate request, the request must have the source with the channel type. 
            The type "dial" used and must be initialized by the call applicant.
        '''
        logger.info("request_handler_originate")
        servername  = request['servername']
        server      = self.servers.get(servername)
        username    = request['user']
        source      = request['source']
        destination = request['destination']
        type        = request['type']
        #
        channel     = source
        context     = server.default_context
        exten       = None
        priority    = None
        timeout     = 15
        callerid    = None
        account     = None
        application = None
        data        = None
        variable    = {}
        async       = True

        originates  = []
        logs        = []

        if type == "internalCall":
            sourceChannel = None
            for sourceChannel in server.status.channels.items():
                tech, chan = sourceChannel.rsplit('-', 1)[0].split('/', 1)
                if chan == source:
                    channel = sourceChannel
                    break

            application = "Dial"
            data        = "%s,30,rTt" % destination
            originates.append((channel, context, exten, priority, timeout, callerid, account, application, data, variable, async))
            logs.append("from %s to %s" % (channel, destination))

        
        if type == "dial":
            tech, peer = source.split('/')
            peer       = server.status.peers.get(tech).get(peer)
            context    = peer.context
            exten      = destination
            priority   = 1
            variable   = dict([i.split('=', 1) for i in peer.variables])
            variable["SIPADDHEADER"]= "Alert-Info: 192.168.3.107\;info=alert-autoanswer\;delay=3"
            originates.append((channel, context, exten, priority, timeout, callerid, account, application, data, variable, async))
            logs.append("from %s to %s@%s timeout %d variable %s" % (channel, exten, context,timeout, variable))
        
        for idx, originate in enumerate(originates):
            channel, context, exten, priority, timeout, callerid, account, application, data, variable, async = originate
            logger.info("Server %s :: Executting Client Action Originate: %s..." % (servername, logs[idx]))
            server.pushTask(server.ami.originate, *originate) \
                .addErrback(self._onAmiCommandFailure, servername, "Error Executting Client Action Originate: %s" % (logs[idx]))

    def request_handler_hangupchannel(self, request):
        ''' Process hangup of the channel '''
        servername  = request['servername']
        channel     = request['channel']
        
        logger.info("Server %s :: Executting client request Hangup: %s..." % (servername, channel))
        server = self.servers.get(servername)
        server.pushTask(server.ami.hangup, channel) \
            .addErrback(self._onAmiCommandFailure, servername, "Error Executting Hangup on Channel: %s" % channel)

    def request_handler_transfer(self, request):
        servername  = request['servername']
        server      = self.servers.get(servername)
        username   = request['user']
        source      = request['source']
        destination = request['destination'] 
        type        = request['type']
        
        channel       = source
        context       = server.default_context
        exten         = destination
        priority      = 1
        extraChannel  = None
        extraExten    = None
        extraContext  = None
        extraPriority = None
        '''
        if type == "meetme":
            extraChannel = action['extrachannel'][0]
            exten        = "%s%s" % (server.meetme_prefix, exten)
            context      = server.meetme_context
            
            if server.version == 1.8: ## Asterisk 1.8 requires some extra params
                extraExten    = exten
                extraContext  = context
                extraPriority = priority
        '''
        logger.info("Server %s :: Executting Client Action Transfer: %s -> %s@%s..." % (servername, channel, exten, context))
        server.pushTask(server.ami.redirect, channel, context, exten, priority, extraChannel, extraContext, extraExten, extraPriority) \
            .addErrback(self._onAmiCommandFailure, servername, "Error Executting Client Action Transfer: %s -> %s@%s" % (channel, exten, context))


    def request_handler_parkchannel(self, request):
        servername  = request['servername']
        server      = self.servers.get(servername)
        channel    = request['channel']
        username   = request['user']
        announce    = request['announce']
        logger.info("Server %s :: Executting Client Action Park: %s from %s..." % (servername, channel, announce))
        server.pushTask(server.ami.park, channel, announce, "") \
        .addErrback(self._onAmiCommandFailure, servername, "Error Executting Client Action Transfer: %s from %s" % (channel, announce))


    def request_handler_get_active_calls(self, request):
        ''' send to the client alls active calls and channels '''
        servername  = request['servername']
        server      = self.servers.get(servername)
        username    = request['user']
        logger.info("Server %s :: Executting client request for alls active calls and channels fo user %s..." % (servername, username))
        logger.info("request_handler_get_server_status")
        tmp        = {}
        servername = request['servername']
        server     = self.servers.get(servername)
        username   = request['user']

        channels=[]
        bridges=[]

        ## Channels
        for uniqueid, channel in server.status.channels.items():
            #tmp[servername]['channels'].append(channel.__dict__)
            channels.append(channel.__dict__)
        #tmp[servername]['channels'].sort(lambda x, y: cmp(x.get('starttime'), y.get('starttime')))
        channels.sort(lambda x, y: cmp(x.get('starttime'), y.get('starttime')))
        ## Bridges
        for uniqueid, bridge in server.status.bridges.items():
            bridge.seconds = [0, int(time.time() - bridge.linktime)][bridge.status == "Link"]
            bridges.append(bridge.__dict__)
        bridges.sort(lambda x, y: cmp(x.get('seconds'), y.get('seconds')))
        bridges.reverse()
        #prepare message to the clients
        to_json={
            "id": "activecalls",
            "username": username,
            "server" : servername,
            "channels" : channels,
            "bridges" : bridges
        }
        #
        if logging.DUMPOBJECTS:
            logger.debug("Object Dump:%s", channels)
            logger.debug("Object Dump:%s", bridges)
        #
        message = json.dumps(to_json, cls=BasicObjectEncoder)
        self._redisPublisher.publish("odin_ami_data_channel", message)
        logger.info("I posted the activecalls message %s to the user." % (username)) 


    def request_handler_request_info(self, request):
        servername  = request['servername']
        server      = self.servers.get(servername)
        command    = request['command']
        username   = request['user']

        def _onResponse(response):
            logger.info("request_handler_request_info , get response %s" % (response))
            #prepare message to the clients
            to_json={
                "id": "requestresponse",
                "username": request['user'],
                "server" : servername,
                "response" : response
            }
            #
            message = json.dumps(to_json, cls=BasicObjectEncoder)
            self._redisPublisher.publish("odin_ami_data_channel", message)
            logger.info("I posted the request_info message to the user %s." % (username))
            #self.http._addUpdate(servername = servername, sessid = session.uid, action = "RequestInfoResponse", response = response)
            
        logger.info("Server %s :: Executting client request : %s..." % (servername, command))
        
        server.pushTask(server.ami.command, command) \
            .addCallbacks(_onResponse, self._onAmiCommandFailure, \
            errbackArgs = (servername, "Error Executting Client Action Request Info '%s'" % command))

    def request_handler_start_monitor(self, request):
        servername = request['servername']
        server = self.servers.get(servername)
        channel = request['channel']
        file = request['file']
        format = request['format']
        logger.debug("request_handler_start_monitor")
        server.pushTask(server.ami.monitor, channel, file, format, 1) \
        .addErrback(self._onAmiCommandFailure, servername, 
            "Error Executting Client Action Start Monitor for the channel %s" % (channel))


    def request_handler_stop_monitor(self, request):
        servername = request['servername']
        server = self.servers.get(servername)
        channel = request['channel']
        logger.debug("request_handler_stop_monitor")
        server.pushTask(server.ami.stopMonitor, channel) \
        .addErrback(self._onAmiCommandFailure, servername, 
            "Error Executting Client Action Stop Monitor for the channel %s" % (channel))

    def request_handler_chan_spy(self, request):
        servername = request['servername']
        server = self.servers.get(servername)
        spyer = request['spyer']
        spyee = request['spyee']
        type = request['type']
        logger.debug("Server %s : Executing chanspy for spyer %s and spyee." %(spyer,spyee))

        channel     = None
        context     = server.default_context
        exten       = None
        priority    = None
        timeout     = None
        callerid    = "Spyer"
        account     = None
        application = "ChanSpy"
        data        = "%s%sqs" % (spyee, [",", "|"][server.version == 1.4])
        variable    = {}
        async       = True
        '''
        '''

        if type == "peer":
            channel = spyer

        if  type == "number":
            channel = "Local/%s@%s" % (spyer, server.default_context)

        #
        server.pushTask(server.ami.originate, channel, context, exten, priority, timeout, callerid, account, application, data, variable, async) \
                .addErrback(self._onAmiCommandFailure, servername, "Error Executting Client Spy Channel: %s -> %s" % (spyer, spyee))
        '''
        server.pushTask(server.ami.originate, channel, context, exten, priority, timeout, callerid, account, application, data, variable, async) \
                .addErrback(self._onAmiCommandFailure, servername, "Error Executting Client Spy Channel: %s -> %s" % (spyer, spyee))
        '''        

    #############################################################################
    ## Actions handlers                                                         #
    #############################################################################
    def process_action(self, action):
        logger.info("I'm processing action : %s" % (action[0])) 

    def client_action_cli_command(self, session, action):
        servername  = action['server'][0]
        command     = action['command'][0]
        
        server = self.servers.get(servername)
        def _onResponse(response):
            ##self.http._addUpdate(servername = servername, sessid = session.uid, action = "CliResponse", response = response)
            pass
        
        logger.info("Server %s :: Executting Client Action CLI Command: %s..." % (servername, command))
        server.pushTask(server.ami.command, command) \
            .addCallbacks(_onResponse, self._onAmiCommandFailure, \
            errbackArgs = (servername, "Error Executting Client Action CLI Command '%s'" % command))


    ##
    ## Request Asterisk Configuration
    ##
    def _onAmiCommandFailure(self, reason, servername, message = None):
        if not message:
            message = "AMI Action Error"
        
        errorMessage = reason.getErrorMessage()
        if type(reason.value) == AMICommandFailure and type(reason.value.args[0]) == type(dict()) and reason.value.args[0].has_key('message'):
            errorMessage = reason.value.args[0].get('message')
        
        logger.error("Server %s :: %s, reason: %s" % (servername, message, errorMessage))
    
    def _requestAsteriskConfig(self, servername):
        logger.info("Server %s :: Requesting Asterisk Configuration..." % servername)
        server = self.servers.get(servername)   

        ## Clear Server Status
        toRemove = []
        '''
        for meetmeroom, meetme in server.status.meetmes.items():
            if not meetme.forced:
                toRemove.append(meetmeroom)
        for meetmeroom in toRemove:
            del server.status.meetmes[meetmeroom]
        '''
        server.status.channels.clear()
        server.status.bridges.clear()
        server.status.queues.clear()
        server.status.queueMembers.clear()
        server.status.queueClients.clear()
        server.status.queueCalls.clear()
        server.status.parkedCalls.clear()
        for channeltype, peers in server.status.peers.items():
            toRemove = []
            for peername, peer in peers.items():
                if not peer.forced:
                    toRemove.append(peername)
            for peername in toRemove:
                del peers[peername]
        
        ## Peers (SIP, IAX) :: Process results via handler_event_peer_entry
        logger.debug("Server %s :: Requesting SIP Peers..." % servername)
        server.pushTask(server.ami.sendDeferred, {'action': 'sippeers'}) \
            .addCallback(server.ami.errorUnlessResponse) \
            .addErrback(self._onAmiCommandFailure, servername, "Error Requesting SIP Peers")
        ##
        logger.debug("Server %s :: Requesting IAX Peers..." % servername)
        server.pushTask(server.ami.sendDeferred, {'action': 'iaxpeers'}) \
            .addCallback(server.ami.errorUnlessResponse) \
            .addErrback(self._onAmiCommandFailure, servername, "Error Requesting IAX Peers")

        ## Run Task Channels Status
        reactor.callWhenRunning(self.taskCheckStatus, servername)

        ##
    ## Tasks
    ##
    def taskCheckStatus(self, servername):
        logger.info("Server %s :: Requesting asterisk status..." % servername)
        server = self.servers.get(servername)

        ## Channels Status
        def onStatusComplete(events):
            logger.debug("Server %s :: Processing channels status..." % servername)
            channelStatus = {}
            callsCounter  = {}
            #Sort channels by uniqueid desc
            events.sort(lambda x, y: cmp(y.get('uniqueid'), x.get('uniqueid')))
            for event in events:
                uniqueid        = event.get('uniqueid')
                channel         = event.get('channel')
                bridgedchannel  = event.get('bridgedchannel', event.get('link'))
                seconds         = int(event.get('seconds', 0))
                
                tech, chan = channel.rsplit('-', 1)[0].split('/', 1)
                try:
                    callsCounter[(tech, chan)] += 1
                except:
                    callsCounter[(tech, chan)] = 1
                
                channelStatus[uniqueid] = None
                channelCreated          = self._createChannel(
                    servername,
                    uniqueid       = uniqueid,
                    channel        = channel,
                    state          = event.get('channelstatedesc', event.get('state')),
                    calleridnum    = event.get('calleridnum'),
                    calleridname   = event.get('calleridname'),
                    _isCheckStatus = True,
                    _log           = "-- By Status Request"
                )
                
                ## Create bridge if not exists
                if channelCreated and bridgedchannel:
                    for bridgeduniqueid, chan in server.status.channels.items():
                        if chan.channel == bridgedchannel:
                            self._createBridge(
                                servername,
                                uniqueid        = uniqueid,
                                bridgeduniqueid = bridgeduniqueid,
                                channel         = channel,
                                bridgedchannel  = bridgedchannel,
                                status          = 'Link',
                                dialtime        = time.time() - seconds,
                                linktime        = time.time() - seconds,
                                seconds         = seconds,
                                _log            = "-- By Status Request"
                            )
                            break
                        
            ## Search for lost channels
            lostChannels = [(k, v.channel) for k, v in server.status.channels.items() if not channelStatus.has_key(k)]
            for uniqueid, channel in lostChannels:
                self._removeChannel(servername, uniqueid = uniqueid, channel = channel, _isLostChannel = True, _log = "-- Lost Channel")
                    
            ## Search for lost bridges
            lostBridges = [
                (b.uniqueid, b.bridgeduniqueid) for b in server.status.bridges.values()
                if not server.status.channels.has_key(b.uniqueid) or not server.status.channels.has_key(b.bridgeduniqueid)
            ]
            for uniqueid, bridgeduniqueid in lostBridges:
                self._removeBridge(servername, uniqueid = uniqueid, bridgeduniqueid = bridgeduniqueid, _isLostBridge = True, _log = "-- Lost Bridge")
            
            ## Update Peer Calls Counter
            for channeltype, peers in server.status.peers.items():
                for peername, peer in peers.items():
                    calls = callsCounter.get((channeltype, peername), 0)
                    if peer.calls != calls:
                        logger.warning("Server %s :: Updating %s/%s calls counter from %d to %d, we lost some AMI events...", servername, channeltype, peername, peer.calls, calls)
                        #self._updatePeer(servername, channeltype = channeltype, peername = peername, calls = calls, _log = "-- Update calls counter (by status request)")
                
            logger.debug("Server %s :: End of channels status..." % servername)


        server.pushTask(server.ami.status) \
            .addCallbacks(onStatusComplete, self._onAmiCommandFailure, errbackArgs = (servername, "Error Requesting Channels Status"))


    ##
    ## Helpers
    ##
    ##

    ## Parked Calls
    def _createParkedCall(self, servername, **kw):
        server     = self.servers.get(servername)
        channel    = kw.get('channel')
        parked     = server.status.parkedCalls.get(channel)
        _log       = kw.get('_log', '')
        
        if not parked:
            parked = BasicObject('ParkedCall')
            parked.channel      = channel
            parked.parkedFrom   = kw.get('from')
            parked.calleridname = kw.get('calleridname')
            parked.calleridnum  = kw.get('calleridnum')
            parked.exten        = kw.get('exten')
            parked.timeout      = int(kw.get('timeout'))
            
            # locate "from" channel
            fromChannel = None
            for uniqueid, fromChannel in server.status.channels.items():
                if parked.parkedFrom == fromChannel.channel:
                    parked.calleridnameFrom = fromChannel.calleridname
                    parked.calleridnumFrom = fromChannel.calleridnum
                    break
            
            logger.debug("Server %s :: ParkedCall create: %s at %s %s", servername, parked.channel, parked.exten, _log)
            server.status.parkedCalls[channel] = parked
            self.__publishMessage(servername, "createparkedcall", "parkedcall", parked)
            if logging.DUMPOBJECTS:
                logging.debug("Object Dump:%s", parked)
        else:
            if not self.isParkedCallStatus:
                logging.warning("Server %s :: ParkedCall already exists: %s at %s", servername, parked.channel, parked.exten)
                
    def _removeParkedCall(self, servername, **kw):
        channel    = kw.get('channel')
        _log       = kw.get('_log', '')
        
        try:
            server = self.servers.get(servername)
            parked = server.status.parkedCalls.get(channel)
            if parked:
                logger.debug("Server %s :: ParkedCall remove: %s at %s %s", servername, parked.channel, parked.exten, _log)
                del server.status.parkedCalls[parked.channel]
                #self.http._addUpdate(servername = servername, action = 'RemoveParkedCall', channel = parked.channel)
                self.__publishMessage(servername, "removeparkedcall", "parkedcall", parked)
                if logging.DUMPOBJECTS:
                    logger.debug("Object Dump:%s", parked)
            else:
                logger.warning("Server %s :: ParkedCall does not exists: %s", servername, channel)
        except:
            logger.exception("Server %s :: Unhandled exception removing ParkedCall: %s", servername, channel)
    
    ## Users/Peers
    def _createPeer(self, servername, **kw):
        server      = self.servers.get(servername)
        channeltype = kw.get('channeltype')
        peername    = kw.get('peername')
        _log        = kw.get('_log', '')
        
        if not server.status.peers.has_key(channeltype) and kw.get('forced', False):
            logger.warning("Server %s :: Adding a not implemented ChannelType %s (forced in config file)", servername, channeltype)
            server.status.peers[channeltype] = {}
        
        if server.status.peers.has_key(channeltype):
            peer = server.status.peers[channeltype].get(peername)
            if not peer:
                peer = BasicObject("User/Peer")
                peer.channeltype = channeltype
                peer.peername    = peername
                peer.channel     = '%s/%s' % (channeltype, peername)
                peer.callerid    = kw.get('callerid', '--')
                peer.forced      = kw.get('forced', False)
                peer.forcedCid   = kw.get('forcedCid', False)
                try:
                    peer.peergroup = server.peergroups[channeltype][peername]
                except:
                    if len(server.peergroups.keys()) > 0:
                        peer.peergroup = "No Group"
            
            peer.context     = kw.get('context', server.default_context)
            peer.variables   = kw.get('variables', [])
            peer.status      = kw.get('status', '--')
            peer.time        = kw.get('time', -1)
            peer.calls       = int(kw.get('calls', 0))

            
            ## Dahdi Specific attributes
            if channeltype == 'DAHDI':
                peer.signalling = kw.get('signalling')
                peer.alarm      = kw.get('alarm', '--')
                peer.dnd        = kw.get('dnd', 'disabled').lower() == 'enabled'
                peer.status     = ['--', peer.alarm][peer.status == '--']
                if peer.callerid == "--":
                    if peer.peername.isdigit():
                        peer.callerid = [peer.channel, "%s %02d" % (peer.signalling, int(peer.peername))][peer.callerid == '--']
                    else:
                        peer.callerid = [peer.channel, "%s %s" % (peer.signalling, peer.peername)][peer.callerid == '--']
                
            ## Khomp
            if channeltype == 'Khomp':
                peer.alarm = kw.get('alarm', '--')
                if peer.callerid == "--":
                    peer.callerid = [peer.callerid, peer.channel][peer.callerid == '--']
                    peer.callerid = [peer.channel, "KGSM %s" % peer.peername]['Signal' in peer.status]
                
            logger.debug("Server %s :: Adding User/Peer %s %s", servername, peer.channel, _log)
            server.status.peers[peer.channeltype][peer.peername] = peer
            
            if logging.DUMPOBJECTS:
                logger.debug("Object Dump:%s", peer)
        else:
            logger.warning("Server %s :: Channeltype %s not implemented in Monast.", servername, channeltype)


    def _updatePeer(self, servername, **kw):
            channeltype = kw.get('channeltype')
            peername    = kw.get('peername')
            _log        = kw.get('_log', '')
            try:
                peer = self.servers.get(servername).status.peers.get(channeltype, {}).get(peername)
                if peer:
                    logger.debug("Server %s :: Updating User/Peer %s/%s %s", servername, channeltype, peername, _log)
                    for k, v in kw.items():
                        if k == '_action':
                            if v == 'increaseCallCounter':
                                peer.calls += 1
                            elif v == 'decreaseCallCounter':
                                peer.calls -= 1
                        # Ignore callerid on forced peers
                        if k == "callerid" and peer.forcedCid:
                            continue
                        # Update peer
                        if k not in ('_log', '_action'): 
                            if peer.__dict__.has_key(k):
                                peer.__dict__[k] = v
                            else:
                                log.warning("Server %s :: User/Peer %s/%s does not have attribute %s", servername, channeltype, peername, k)
                    #prepare message to the clients
                    #to_json={"id": "updatepeer", "server": servername, "peer" : peer}
                    #message = json.dumps(to_json, cls=BasicObjectEncoder)
                    #self._redisPublisher.publish("odin_ami_data_channel", message)
                    self.__publishMessage(servername, "updatepeer", "peer", peer)
                else:
                    logger.warning("Server %s :: User/Peer not found: %s/%s", servername, channeltype, peername)
            except:
                logger.exception("Server %s :: Unhandled exception updating User/Peer: %s/%s", servername, channeltype, peername)