# 
# F1COM server twisted based.
# The server is a bridge beetwen a client(or clients) F1COM and an Asterisk serveur dispatcher 
# The AMI dispatcher implemented by an external serveur, please see amidispatcher.py and run with runamidispatcher.py
# Network data exchange implemeted by json messages by REDIS message queue
# 
#
import os
import sys
import re
import time
import logging
import optparse
import signal
import json
import sys, warnings
import struct
from commons import BasicObject, BasicObjectEncoder, OdinConfigParser, AsteriskHelper
from ConfigParser import NoOptionError
from callcenter import CallCenter

#logger initialized by main runner module
logger = logging.getLogger("odin_f1com");

try:
    from twisted.python import log
    from twisted.internet import reactor, protocol
    from twisted.internet.protocol import ServerFactory
    from twisted.protocols.basic import _PauseableMixin
    from twisted.python import failure
    from twisted.internet import reactor, task, defer
    from twisted.internet import error as tw_error
    from twisted.application import internet
    from twisted.application import service
    from twisted.internet.defer import inlineCallbacks

except ImportError:
    print "PYF1COM: Module twisted not found."
    print "You need twisted matrix 10.1+ to run AMIWORKER. Get it from http://twistedmatrix.com/"
    sys.exit(1)

try:
    import json
except ImportError:
    print "PYF1COM ERROR: Can't import json."
    sys.exit(1)
#
#gloval variables
MY_SITE_IDENTIFICATION="F1COMAMI"
MY_ALARM_SPAN = "SPANAL"
#Indicate that some F1COM messages can'be changed
F1_COMPATIBLE=True
#
class F1ComProtocol(protocol.Protocol, _PauseableMixin):
    """This is just about the simplest possible protocol"""
    __msg_buffer = ""

    def __init__(self, factory):
        self.factory = factory;

    def connectionMade(self):
        self.factory.f1ComClient.append(self)
        d = self.transport.getPeer()
        logger.info("F1ComProtocol : New connection from [%s:%s] added to the factory." % (d.host, d.port))

    def dataReceived(self, data):
        logger.debug("F1ComProtocol : New data [ %s ] of length %i " %(data.encode('hex'), len(data)))
        self.__msg_buffer = self.__msg_buffer + data
        try:
            #check the length of the data
            while len(self.__msg_buffer) > 11 and not self.paused:
                (type,) = struct.unpack("b", self.__msg_buffer[9])
                #
                (length,) = struct.unpack("b", self.__msg_buffer[10])
                #
                message = self.__msg_buffer[:11 +length]
                # 
                handler = None
                try:
                    #look for a handler. If the handler is not existe throw an exception.
                    handler = getattr(self, 'handler_type' + hex(type))
                except Exception,e:
                    logging.warning("F1ComProtocol : Get an exception [%s]. Can't find handler for the type [0x%x]." % (e,type))
                
                if handler : 
                    logger.debug("F1ComProtocol : Call handler_type0x%x ." % (type))
                    logger.debug("F1ComProtocol : Data passed to the handler [ %s ] of length %i " %(data.encode('hex'), len(data)))
                    handler(message)
                else :
                    logger.debug("F1ComProtocol : Can't find handler for x%x message type " % (type))
                # delete Message type chunk 
                self.__msg_buffer = self.__msg_buffer[11+length:]
                #logger.debug("F1ComProtocol : Temp buffer  after process Message type %s." % (temp))
                #self.__msg_buffer = temp
                logger.debug("F1ComProtocol : Msg buffer after process processing [ %s ]." % (self.__msg_buffer))
            #end while
        except Exception,e:
            logging.error("F1ComProtocol : Get an exception [%s]. Must close the connection " % (e))
            self.transport.loseConnection()

    def connectionLost(self, reason):
        d = self.transport.getPeer()
        logger.info("F1ComProtocol : Connection lost , I remove myself [%s:%s] from factory." % (d.host, d.port))
        self.factory.f1ComClient.remove(self)


    #
    # message handlers
    #
    def handler_type0x1e(self, message):
        logger.debug("F1ComProtocol : Message 0x1e skipped.")

    def handler_type0x11(self, message):
        logger.debug("F1ComProtocol : Message 0x11.")

    def handler_type0x1a(self,packet):
        logger.debug("F1ComProtocol : Begin process the server originate call message :  0x1A.")
        (length,) = struct.unpack("b", packet[10])
        message = packet[11:11 +length]
        #
        if len(message) == 27:
            dest = message[3:23].strip()
            src  = message[23:27]
            self.factory.originate_call(src, dest)
            self.send_ack_alarm_event(0x31)
        else :
            #it is a workaround for Message type from F1Com client refused
            raise Exception("F1ComProtocol : Message type [%s] EXT CALL has wrong length [%i]." % (message,len(message)))

    def handler_type0x1C(self, packet):
        logger.debug("F1ComProtocol : Begin process the server hangup message :  0x1C.")
        (length,) = struct.unpack("b", packet[10])
        message = packet[11:11 +length]
        if len(message) == 27:
            dest = message[3:23].strip()
            src  = message[23:27]
            done = self.factory.hangup_call(src, dest)
            if done :
                self.send_ack_alarm_event(0x31)
            else:
                self.send_ack_alarm_event(0x30)
            logger.debug("F1ComProtocol : Message type 0x1C : hangup the source %s with destination is done %s ." % (src, dest, done))
        else :
            #it is a workaround for Message type from F1Com client refused
            raise Exception("Message type 0x1c [%s] has wrong length [%i]." % (message,len(message)))

    def handler_type0x12(self,packet):
        logger.debug("F1ComProtocol : Begin process the server polling message : 0x12.")
        (length,) = struct.unpack("b", packet[10])
        message = packet[11:11 +length]
        self.send_polling_response(0x31)

    def handler_type0x2a(self, packet):
        '''
        TODO : check the possibility to get more that one number in the message
        '''
        logger.debug("F1ComProtocol : Begin process the server message :  for close all call.")
        (length,) = struct.unpack("b", packet[10])
        message = packet[11:11 +length]
        if len(message) > 0:
            src  = message
            done = self.factory.hangup_call(src, "")
            if done :
                self.send_ack_alarm_event(0x31)
            else:
                self.send_ack_alarm_event(0x30)
            logger.debug("F1ComProtocol : Message type 0x2A : hangup %s is done %s ." % (src, done))
        else :
            #it is a workaround for Message type from F1Com client refused
            raise Exception("F1ComProtocol : Message type 0x2a [%s] to close all calls has wrong length [%i]." % (message,len(message)))

    def handler_type0x28(self, packet):
        logger.debug("Begin process the server message :  park call message.")
        #(length,) = struct.unpack("b", packet[10])
        eom = packet.find('\x00', packet)
        number = eom[11:]
        logger.debug("F1ComProtocol : Park call for the number [%s]." % (number))
        if len(number) > 0:
            #number = message[0:len(message)].strip()
            done   = self.factory.park_call(number)
            if done :
                self.send_ack_alarm_event(0x31)
            else:
                self.send_ack_alarm_event(0x30)
            logger.debug("F1ComProtocol : Message type 0x28 : park %s is done %s ." % (number, done))
        else:
            #
            raise Exception("F1ComProtocol : Message type 0x28 [%s] : park a call has the wrong length [%i]." % (message, len(message)))

    def handler_type0x29(self, packet):
        logger.debug("F1ComProtocol : Begin process the server message :  commut message")
        (length,) = struct.unpack("b", packet[10])
        message = packet
        if len(message) > 0:
            callref = message[0:8]
            internal = message[10:14]
            done = self.factory.commut_call(internal, callref)
            if done :
                self.send_ack_alarm_event(0x31)
            else:
                self.send_ack_alarm_event(0x30)
            logger.debug("F1ComProtocol : Message type 0x29 : commut the internal %s with the external %s done %s ." % (internal, callref, done))
        else:
            #
            raise Exception("F1ComProtocol : Message type 0x29 [%s] to commut a call has the wrong length [%i]." % (message, len(message)))

    def handler_type0x36(self, packet):
        logger.debug("F1ComProtocol : Begin process the server message hangup a call.")
        (length,) = struct.unpack("b", packet[10])
        #message = packet[:11 +length]
        callref = packet[:8]
        if callref[0] == '@':
            logger.debug("F1ComProtocol : Hangup a call by the callref [%s]." % (callref))
            done = self.factory.hangup_call_by_callref(callref)
        else:
            number = packet[11:11+length]
            logger.debug("F1ComProtocol : Hangup a call by the caller or called number [%s]." % (number))
            done = self.factory.hangup_call(number,'')
        #send the notification to the M1Server
        if done:
            self.send_ack_alarm_event(0x31)
        else:
            self.send_ack_alarm_event(0x30)
        


    def send_polling_response(self, acknack):
        ''' 
        Send ack/nack respons of the F1-External system polling 
        '''
        response = MY_SITE_IDENTIFICATION
        response += struct.pack("b", 0x31)
        response += struct.pack("b", 0x13)
        response += struct.pack("b", 0x0A)
        response += 'QQQ'
        response += 'HHMMSS'
        response += struct.pack("b", acknack)
        logger.debug("F1ComProtocol : Send the polling response : [ %s ]" % (response.encode('hex')))
        self.transport.write(response)

    def send_ack_alarm_event(self, acknack):
        '''
        Send the ack response for a alarm event
        '''
        response = MY_SITE_IDENTIFICATION
        response += struct.pack("b", 0x31)
        response += struct.pack("b", 0x11)
        response += struct.pack("b", 0x01)
        response += struct.pack("b", acknack)
        logger.debug("F1ComProtocol : Send the alarm acknowledgement event : [ %s ] " % (response))
        self.transport.write(response)

    def send_result_ext_call(self, callState, dest):
        ''' 
        Send the states of the an externall call
        '''
        '''
        avoid unicode and fill with space in the case of F1 compatible mode
        F1 implements F1COM protocol for the message 0x1B without space on the right
        '''        
        if F1_COMPATIBLE:
            rightDestNumber = dest.encode('utf-8')
        else:
            rightDestNumber = dest.ljust(20).encode('utf-8')
        length = len(rightDestNumber) + 1
        response = "EXT CALL"
        response += struct.pack("b", 0x4E)
        response += struct.pack("b", 0x1B)
        response += struct.pack("b", length)
        response += struct.pack("b", callState)
        response += rightDestNumber
        self.transport.write(response)
        logger.debug("F1ComProtocol : Sent the EXT CALL state  [ %s ] to the F1COM client." % (response.encode('hex')))

    def send_alarm_event(self, type, code, pstn, optionalInfo):
        '''
        Send an alarm event to the F1COM client
        '''
        length = 17 + len(optionalInfo)
        response  = MY_SITE_IDENTIFICATION
        response += struct.pack("b", 0x30)
        response += struct.pack("b", 0x10) #event id
        response += struct.pack("b", length)
        response += 'QQQ'
        response += 'HHMMSS'
        response += type
        response += code.encode('utf-8')
        response += pstn
        response += optionalInfo.encode('utf-8')
        logger.debug("F1ComProtocol : Send the alarm event : [ %s ] " % (response.encode('hex')))
        self.transport.write(response)


    

class F1ComFactory(ServerFactory):
    """docstring for ClassName"""
    protocol = F1ComProtocol

    def __init__(self):
        self.f1ComClient = []


    def buildProtocol(self, adr):
        return F1ComProtocol(self)

    def set_ami_worker(self,f1comworker):
        self.f1comworker = f1comworker

    def originate_call(self, src, dest):
        logger.debug("F1ComFactory :  originate call from %s to %s"%(src,dest))
        if self.f1comworker != None:
            self.f1comworker.originate_call(src,dest)
        else:
            logger.error("F1ComFactory  : Can't originate call cause the f1comworker instance is not valid.")

    def hangup_call(self, src, dest):
        logger.debug("F1ComFactory : hangup_call from %s to %s"%(src,dest))
        if self.f1comworker != None:
            return self.f1comworker.hangup_call(src,dest)
        else:
            logger.error("F1ComFactory :  Can't hangup call the f1comworker instance is not valid.")

    def hangup_call_by_callref(self, callref):
        logger.debug("F1ComFactory : hangup_call by callref %s"%(callref))
        done = False
        if self.f1comworker != None:
            done = self.f1comworker.hangup_call_by_callref(callref)
        else:
            logger.error("F1ComFactory :  Can't hangup call by callref the f1comworker instance is not valid.")
        return done

    def park_call(self, number):
        logger.debug("F1ComProtocol : Park_call from %s."%(number))
        done = False
        if self.f1comworker != None:
            done = self.f1comworker.park_call(number)
        else:
           logger.error("F1ComProtocol : Can't park call the f1comworker instance is not valid.") 
        return done

    def commut_call(self, internal, external):
        logger.debug("F1ComProtocol : Commut_call from the external number %s to the internal from %s."%(external,internal))
        done = False
        if self.f1comworker != None:
            done = self.f1comworker.commut_call(internal, external)
        else:
            logger.error("F1ComProtocol : Can't commut call the f1comworker instance is not valid.")
        return done

    #FCOM1 messages senders
    def send_result_ext_call(self, state, dest):
        for f1ComClient in self.f1ComClient:
            f1ComClient.send_result_ext_call(state, dest)

    def send_alarm_event(self, type, code, pstn, optionalInfo):
        for f1ComClient in self.f1ComClient:
            f1ComClient.send_alarm_event(type, code, pstn, optionalInfo)


class AMIBridge(object):
    def __init__(self, config, redisPublisher):
        super(AMIBridge, self).__init__()
        ## Initialize logger
        global logger
        #
        global MY_SITE_IDENTIFICATION
        global MY_ALARM_SPAN
        try:
            MY_SITE_IDENTIFICATION = config.get("global","site_id")
        except NoOptionError:
            logger.warning("AMIBridge : Parameter site_id missing. \
                Please check the configuration file odinf1com.conf. Value site_id missing from the section global")
        #
        try:
            MY_ALARM_SPAN = config.get('f1com', 'alarm_span_code')
        except NoOptionError:
            logger.warning("AMIBridge : Parameter site_id missing. \
                Please check the configuration file odinf1com.conf. Value site_id missing from the section global")
        #
        self._redisPublisher = redisPublisher
        self.originateCalls = {}
        self.channels       = {}
        self.bridgedCalls   = {}
        self.parkedCalls    = {}
        #
        self._callCenter    = CallCenter(self)
        #
        try:
            self._asteriskServer = config.get("global", "asterisk")
        except NoOptionError:
            logger.error("AMIBridge : Parameter asterisk missing. \
                Please check the configuration file odinf1com.conf. Value asterisk missing from the section global")
            reactor.stop()
        #
        self.amiDataHandlers = {
            'createchannel'    : self.handler_ami_createchannel,
            'updatechannel'    : self.handler_ami_updatechannel,
            'removechannel'    : self.handler_ami_removechannel,
            'createbridge'     : self.handler_ami_createbridge,
            'updatebridge'     : self.handler_ami_updatebridge,
            'removebridge'     : self.handler_ami_removebridge,
            'updatepeer'       : self.handler_ami_updatepeer,
            'createparkedcall' : self.handler_ami_createparkedcall,
            'removeparkedcall' : self.handler_ami_removeparkedcall,
            'userevent'        : self.handler_ami_userevent,
            'alarm'            : self.handler_ami_alarm

        }

    def stop(self):
        logger.debug("AMIBridge : Stopped.")

    def set_f1com_factory(self, factory):
        self.f1ComFactory = factory

    def process_ami_data(self, data):
        logger.debug("AMIBridge : Get data from ami worker")
        request = json.loads(data)
        requestId = request['id']
        if id == None:
            logger.error("AMIBridge : Cant' find request id, the request ignored.")
            return
        logger.info("I'm processing request : %s" % (requestId))
        handler = self.amiDataHandlers.get(requestId)
        if handler:
            reactor.callWhenRunning(handler, request)
        else:
            logger.error("AMIBridge : Can't find the request handler %s" %(requestId))

    #Helpers

    def _look_for_channel_by_uniqueid(self, uniqueid):
        '''
        '''
        channel = None
        for i in self.channels.keys():
            chan = self.channels[i]
            if uniqueid == chan.uniqueid:
                channel = chan
                logger.debug("AMIBridge : Get the channel %s for uniqueid %s." % (chan.channel, chan.uniqueid))
                break
        #
        return channel

    def _set_callerid_for_bridge(self, bridge):
        '''
        '''
        channel = self._look_for_channel_by_uniqueid(bridge.uniqueid)
        if channel:
            bridge.calleridnum = channel.calleridnum
            bridge.calleridname = channel.calleridname
        else:
           logger.debug("AMIBridge : Can't find originate channel %s for the bridge uniqueid %s." % (bridge.channel, bridge.uniqueid))
        #
        bridgedChannel = self._look_for_channel_by_uniqueid(bridge.bridgeduniqueid)
        if bridgedChannel:
            bridge.bridgecalleridnum = bridgedChannel.calleridnum
            bridge.bridgecalleridname = bridgedChannel.calleridname
        else:
            logger.debug("AMIBridge : Can't find bridged channel %s for the bridge uniqueid %s." % (bridge.bridgedchannel, bridge.bridgeduniqueid))

    def _look_for_call_by_number(self, number):
        '''
        Look for a call by the number
        First pass look into bridgedCalls by channel(the source of the call)
        Second pass look into bridgedCalls by bridgedchannel(the destination of the call) 
        On success return the tuple bridgedchannel and channel
        TODO :  remplace by one time pass
        '''
        channel = None
        bridgedchannel = None
        for i in self.bridgedCalls.keys():
            bridge = self.bridgedCalls[i]
            logger.debug("AMIBridge : Look for the  bridgecalleridnum %s and compare with %s." % (bridge.bridgecalleridnum, number))
            if bridge.bridgecalleridnum == number:
                channel = bridge.channel
                bridgedchannel = bridge.bridgedchannel
                break
        if not channel:
            for i in self.bridgedCalls.keys():
                bridge = self.bridgedCalls[i]
                logger.debug("AMIBridge : Look for(second pass) the  bridgecalleridnum %s and compare with %s. ." % (bridge.calleridnum, number))
                if bridge.calleridnum == number:
                    channel = bridge.bridgedchannel
                    bridgedchannel = bridge.channel
                    break
        #
        return (bridgedchannel, channel)


    def _createChannel(self, data):
        #
        createChannel = data['channel']
        uniqueid = createChannel['uniqueid']
        channel = createChannel['channel']
        if not self.channels.has_key(uniqueid):
            #
            newChannel = BasicObject("Channel")
            newChannel.uniqueid     = uniqueid
            newChannel.channel      = channel
            newChannel.state        = createChannel['state']
            newChannel.calleridnum  = createChannel['calleridnum']
            newChannel.calleridname = createChannel['calleridname']
            newChannel.monitor      = createChannel['monitor']
            newChannel.spy          = createChannel['spy']
            newChannel.starttime    = time.time()
            self.channels[uniqueid] = newChannel
        else:
            logger.warning("AMIBridge : Channel %s with unique id %s already exists." %(channel, uniqueid))

    def _updateChannel(self, data):
        #
        updateChannel = data['channel']
        channel = updateChannel['channel']
        uniqueid = updateChannel['uniqueid']
        try:
            chan = self.channels.get(uniqueid)
            if chan:
                logger.debug("Channel update : %s." % (channel))
                for k, v in updateChannel.items():
                    if chan.__dict__.has_key(k):
                        chan.__dict__[k] = v
                    else:
                        logger.warning("AMIBridge : Channel %s does not have attribute %s" % (channel, k))
                if logging.DUMPOBJECTS:
                    logger.debug("AMIBridge : Channel updated :%s", chan)
                #udpate incall state
                self._callCenter.udpate_call_from_channel(chan)
            else:
                logger.warning("AMIBridge : Channel not found: %s." % (channel))
        except:
            logger.exception("AMIBridge : Channel Unhandled exception updating channel: %s." % (channel))

    def _removeChannel(self, data):
        #
        uniqueid = data['channel']['uniqueid']
        channel = data['channel']['channel']
        if self.channels.has_key(uniqueid):
            del self.channels[uniqueid]
            logger.debug("AMIBridge : Channel %s with the uniqueid %s removed." %(channel, uniqueid))
            self._callCenter.check_and_remove_call(uniqueid)
        else:
            logger.warning("AMIBridge : Can't find and remove the channel %s with unique id %s." %(channel, uniqueid))

        
    #F1Com commands part
    def originate_call(self, src, dest):
        '''
        Origiante a call from src, I add the technologie to the src 
        cause F1Com protocol don't carry aboit it
        TODO : Must look for the solution for indicate the technologie
        '''
        tech = "SIP"
        peer = tech + "/" + src
        to_json = {"id": "originate", "servername": self._asteriskServer, "type": "dial", 
        "user": "f1comami", "source": peer, "destination": dest}
        message = json.dumps(to_json)
        self._redisPublisher.publish("odin_ami_request_channel", message)
        #originateCall = OriginateCall({'src': src, 'dest': dest})
        originateCall = BasicObject("OriginateCall")
        originateCall.src = src
        originateCall.dest = dest
        #Set the key as the source number, the key will be migrate to uniqueid into create channel handler
        self.originateCalls[src] = originateCall #OriginateCall({'src': src, 'dest': dest})
        logger.debug("AMIBridge : Originate call from %s to %s " % (src,dest))

    def transffer_call(self, channel, ext):
        to_json = {"id": "transfer", "servername": self._asteriskServer, "type": "dial", "user": "f1comami", "source": channel, "destination": ext}
        message = json.dumps(to_json)
        self._redisPublisher.publish("odin_ami_request_channel", message)
    
    def __hangup_call_by_number(self, number):
        '''
        Look for a call by number
        If the call existe send a message to hangup the call
        '''
        done = False
        bridgedchannel, channel = self._look_for_call_by_number(number)
        if channel:
            to_json = {"id": 'hangupchannel', "servername": self._asteriskServer , "user": "f1comami", 
                "channel": channel}
            message = json.dumps(to_json)
            self._redisPublisher.publish("odin_ami_request_channel", message)
            done = True

        return done

    def hangup_call(self, src, dest):
        '''
        Look for a call by src into the bridged calls
        I the call is not located look for destination number 
        '''
        done = False 
        #
        done = self.__hangup_call_by_number(src)
        if done == False and len(dest):
            ''' try by destination '''
            done = self.__hangup_call_by_number(dest)
            
        if done :
            logger.debug("AMIBridge : Call located and hangup sent to the iPBX for the call with the source number %s." % (src))
        else:
            logger.warning("AMIBridge : Call can't be located for hangup with the source number %s." % (src))
        return done

    def hangup_call_by_callref(self, callref):
        logger.debug("AMIBridge : Hangup call by callref [ %s ]. " % (callref))
        channel = self._callCenter.get_channel_by_callref(callref)
        done = False
        if channel:
            to_json = {"id": 'hangupchannel', "servername": self._asteriskServer, "user": "f1comami", 
                "channel": channel}
            message = json.dumps(to_json)
            self._redisPublisher.publish("odin_ami_request_channel", message)
            done = True
        else:
            logger.warning("AMIBridge : Can't find a call for the callref %s." % (callref))

        return done


    def park_call(self, number):
        '''
        Park a call by the called phone number , the call looked into bridged calls map
        It is a future of the F1COM protocol the channel is not used.
        '''
        logger.info("AMIBridge : Looking an active call for the number and try to park." % (number))
        done = False
        bridgedchannel, channel = self._look_for_call_by_number(number)
        if channel:
            to_json = {"id": 'parkchannel', "servername": self._asteriskServer, "user": "f1comami", 
                "channel": bridgedchannel, "announce" :  channel}
            message = json.dumps(to_json)
            self._redisPublisher.publish("odin_ami_request_channel", message)
            done = True
 
        #check if the call existe and return value
        if done == True:
            logger.warning("AMIBridge : Park the call for the number %s." % (number)) 
        else:
            logger.warning("AMIBridge : Park call the number is not parked , can't find the active call for the number %s." % (number))  
        return done

    def commut_call(self, internal, external):
        '''
        Commut an internal extention to the parked call by the parked extention
        Please see the configuration of the asterisk box and parkedcalls context 
        External can have two types of information :
            Reference of a call if begin with @, it is a incomming call and processed by Call Center module
            Otherwise this is an external number and looked into parked calls
        '''
        done = False
        parkedExten = None
        if external[0] == '@':
            #
            done = self._callCenter.commut_call(internal, external)
            if done == True:
                return done
        #
        for i in self.parkedCalls.keys():
            parkedCall = self.parkedCalls[i]
            if parkedCall.calleridnum == external:
                parkedExten = parkedCall.exten
                break
        #so far so good
        if parkedExten:
            self.originate_call(internal, parkedExten)
            logger.debug("AMIBridge : Call commuted for the internal %s to the external %s by the parked extention %s." % 
                (internal, external, parkedExten))
            done = True
        else:
            logger.debug("AMIBridge : Call can't be commuted for the internal %s and the external %s." %(internal, external))

        return done

    def send_alarm_event(self, type, code, pstn, optional):
        if self.f1ComFactory:
            self.f1ComFactory.send_alarm_event(type, code, pstn, optional)
        else:
            logger.error("AMIBridge : Alarm event can't be send to F1COM clients.")


    def __send_callcenter_event(self, code, extention, callcenter, callref, caller, post=""):
        '''
        Send a callcenter message to F1COM clients for indicate the state if an incomming call
        '''
        logger.debug("AMIBridge : __send_callcenter_message [ %s %s %s %s ]" % (extention, callcenter, callref, caller))
        if self.f1ComFactory:
            type     = "1"
            pstn     = "1"
            optional ="#SDA=" + extention
            if len(post) > 0:
                optional +="#POSTE=" + extention
            optional +="#IDCOMM=" + callref
            optional +="#CALLCENTER=" + callcenter
            optional +="#APPELANT=" + caller
            optional += "#AT=F1#NOMENT=27"
            self.f1ComFactory.send_alarm_event(type, code, pstn, optional)
        else:
            logger.error("AMIBridge : CallCenter event can't be send to F1COM clients.")
        


    def __process_incomming_call(self, data):
        logger.debug("AMIBridge : __process_incomming_call %s " % (data))
        self._callCenter.new_call(data)

    #AMI handlers 
    def handler_ami_updatepeer(self, data):
        pass

    def _send_call_state(self, state, dest):
        if self.f1ComFactory:
            self.f1ComFactory.send_result_ext_call(state, dest)
            logger.debug("AMIBridge : _send_call_state send %c for the destination %s to the F1 clients " % (state, dest))
        else:
            logger.debug("AMIBridge : handler_ami_createchannel can't find into originate calls")

    def handler_ami_createchannel(self, data):
        logger.debug("AMIBridge : handler_ami_createchannel ")
        calleridnum = data['channel']['calleridnum']
        if self.originateCalls.has_key(calleridnum):
            originateCall = self.originateCalls[calleridnum]
            uniqueid = data['channel']['uniqueid']
            self.originateCalls[uniqueid] = originateCall
            originateCall.bridgedStatus =""
            del  self.originateCalls[calleridnum]
            originateCall.srcChannel = data['channel']['uniqueid']
            self._send_call_state(0x30, originateCall.dest)
        else:
            logger.debug("AMIBridge : handler_ami_createchannel can't find into originate calls")
        #
        self._createChannel(data)


    def handler_ami_updatechannel(self, data):
        logger.debug("AMIBridge : handler_ami_updatechannel")
        self._updateChannel(data)

    def handler_ami_removechannel(self, data):
        logger.debug("AMIBridge : handler_ami_removechannel")
        uniqueid = data['channel']['uniqueid']
        if self.originateCalls.has_key(uniqueid):
            originateCall = self.originateCalls[uniqueid]
            callState = 0x33
            if originateCall.bridgedStatus == 'Link':
                callState=0x33                
            elif originateCall.bridgedStatus == 'Dial':
                callState=0x43
            #
            dest = self.originateCalls[uniqueid].dest
            self._send_call_state(callState, dest)
            #cleanup call from the table 
            del  self.originateCalls[uniqueid]

        else:
            logger.debug("AMIBridge : handler_ami_removechannel can't find into originate calls")
        #
        self._removeChannel(data)


    def handler_ami_createbridge(self, data):
        logger.debug("AMIBridge handler_ami_createbridge")
        uniqueid = data['bridge']['uniqueid']
        bridgeduniqueid = data['bridge']['bridgeduniqueid']
        if self.originateCalls.has_key(uniqueid):
            originateCall = self.originateCalls[uniqueid]
            originateCall.srcChannel = data['bridge']['uniqueid']
            originateCall.bridgetChannel = data['bridge']['bridgedchannel']
            originateCall.bridgetUniqueId = data['bridge']['bridgeduniqueid']
            bridgedStatus = data['bridge']['status']
            originateCall.bridgedStatus = bridgedStatus
            if bridgedStatus == 'Dial':
                self._send_call_state(0x31, self.originateCalls[uniqueid].dest)
            else:
                logger.debug("AMIBridge : handler_ami_createbridge skip to send the status %s to F1" % (bridgedStatus))
        else:
            logger.debug("AMIBridge : handler_ami_createbridge can't find into originate calls")
        #create bridged call
        bridgekey       = (uniqueid, bridgeduniqueid)
        if not self.bridgedCalls.has_key(bridgekey):
            '''
            '''
            bridge = BasicObject("Bridge")
            bridge.uniqueid        = uniqueid
            bridge.bridgeduniqueid = data['bridge']['bridgeduniqueid']
            bridge.channel         = data['bridge']['channel']
            bridge.bridgedchannel  = data['bridge']['bridgedchannel']
            bridge.status          = data['bridge']['status']
            bridge.dialtime        = data['bridge']['dialtime']
            #bridge.linktime        = data['bridge']['linktime']
            self._set_callerid_for_bridge(bridge)
            if logging.DUMPOBJECTS:
                logger.debug("Bridge create :%s", bridge)
            self.bridgedCalls[bridgekey] = bridge
            #update an incomming call if existe
            self._callCenter.update_call_from_bridge(bridge)
        else:
            logger.warning("AMIBridge : bridge call already existe %s with %s" %
             (data['bridge']['channel'], data['bridge']['bridgedchannel']))




    def handler_ami_updatebridge(self, data):
        logger.debug("AMIBridge handler_ami_updatebridge")
        uniqueid = data['bridge']['uniqueid']
        bridgeduniqueid = data['bridge']['bridgeduniqueid']
        bridgedStatus = data['bridge']['status']
        if self.originateCalls.has_key(uniqueid):
            originateCall = self.originateCalls[uniqueid]            
            #
            if bridgedStatus != originateCall.bridgedStatus :
                originateCall.bridgedStatus = bridgedStatus
                if bridgedStatus == 'Link':
                    self._send_call_state(0x32, self.originateCalls[uniqueid].dest)
                else:
                    logger.debug("AMIBridge : handler_ami_createbridge skip to send the status %s to F1" % (bridgedStatus))
        else:
            logger.debug("AMIBridge : handler_ami_updatebridge can't find into originate calls")
        #
        bridgekey       = (uniqueid, bridgeduniqueid)
        bridge = self.bridgedCalls.get(bridgekey)
        if bridge:
            bridge.status = data['bridge']['status']
            bridge.linktime = data['bridge']['linktime']
            #Set caller and called ids
            self._set_callerid_for_bridge(bridge)
            #check if the call is incomming
            self._callCenter.update_call_from_bridge(bridge)
            if logging.DUMPOBJECTS:
                    logger.debug("Bridge updated :%s", bridge)
        
        

    def handler_ami_removebridge(self, data):
        logger.debug("AMIBridge handler_ami_removebridge")
        uniqueid = data['bridge']['uniqueid']
        bridgeduniqueid = data['bridge']['bridgeduniqueid']
        if self.originateCalls.has_key(uniqueid):
            originateCall = self.originateCalls[uniqueid]
            callState = 0x33
            dest = self.originateCalls[uniqueid].dest
            self._send_call_state(callState, dest)
            #cleanup call from the table 
            del  self.originateCalls[uniqueid]
            logger.debug("AMIBridge : handler_ami_removebridge originate call for [%s] uniqueid removed." %(uniqueid))
        else:
            logger.debug("AMIBridge : handler_ami_removebridge can't find an originate call for uniqueid [%s]." %(uniqueid))
        #
        bridgekey       = (uniqueid, bridgeduniqueid)
        bridgekey       = (uniqueid, bridgeduniqueid)
        bridge = self.bridgedCalls.get(bridgekey)
        if bridge:
            #
            #check if the call is incomming
            self._callCenter.remove_call(bridge)
            del self.bridgedCalls[bridgekey]
            logger.warning("AMIBridge : handler_ami_removebridge a call removed %s with %s" %
             (data['bridge']['channel'], data['bridge']['bridgedchannel']))

    def handler_ami_createparkedcall(self, data):
        logger.debug("AMIBridge handler_ami_createparkedcall")
        channel = data['parkedcall']['channel']
        parked  = self.parkedCalls.get(channel)
        if not parked :
            parked = BasicObject("ParkedCall")
            #populate the parked 
            parked.channel = channel
            parked.exten =  data['parkedcall']['exten']
            parked.channelFrom = data['parkedcall']['parkedFrom']
            parked.calleridnum = data['parkedcall']['calleridnum']
            parked.calleridnumFrom = data['parkedcall']['calleridnumFrom']
            parked.timeout = data['parkedcall']['timeout']
            parked.calleridname = data['parkedcall']['calleridname']
            parked.calleridnameFrom = data['parkedcall']['calleridnameFrom']
            self.parkedCalls[channel] = parked


    def handler_ami_removeparkedcall(self, data):
        logger.debug("AMIBridge : handler_ami_removeparkedcall %s " % (data))
        channel = data['parkedcall']['channel']
        parked = self.parkedCalls.get(channel)
        if parked :
            del self.parkedCalls[parked.channel]
            logger.debug("AMIBridge : handler_ami_removeparkedcall the parked channel %s removed." % (parked.channel))

    def handler_ami_userevent(self, data):
        '''
        Handler for user event from asterisk dialplan
        Therea are different type of events to idicate what I must do :-)
        AMI is boss for me 
        '''        
        type = data['event']['type']
        if type == 'incommingcall':
            self.__process_incomming_call(data)


    def handler_ami_alarm(self, data):
        '''
        Handler for alarm events from asterisk
        '''
        eventType = data['alarmevent']['event']
        type = '0'
        pstn = '1'
        code = "SPANAL"
        if eventType == 'SpanAlarm':
            type = '1'

        elif eventType == 'SpanAlarmClear':
            type = '2'
        else:
            logger.warning("AMIBridge : handler_ami_alarm can not find type for the alarm event [%s]."% (data))
            return
        #
        optional = "#SITE=%s#TEXT=%s" % (data['server'], '%s')
        self.send_alarm_event(type, code, pstn,optional)
#
