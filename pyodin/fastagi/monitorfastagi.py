#! /usr/bin/env python
'''
exten = _4XXX,1,NoOp(from-trixbox-be-by-sda)
same => n,Set(TIMEOUT(absolute)=300)
same => n,UserEvent(incommingcall,Context:from-trixbox-be,extention:${EXTEN},calleridnum:${CALLERID(num)},calleridname:${CALLERID(name)},uniqueid: ${CDR(uniqueid)})
;same => n,SIPAddHeader(Call-Info: 192.168.3.107\;answer-after=3)
;same => n,SIPAddHeader(Alert-Info: 192.168.3.107\;info=alert-autoanswer\;delay=3)
same => n,AGI(agi://127.0.0.1:4575)
same => n,Hangup()
;same => n,Dial(SIP/6000)

Can be a useful link
https://github.com/lorea/rtcheckcalls/tree/master/obelisk

'''

"""Provide a trivial date-and-time service"""
import os
import sys
from twisted.internet import reactor,protocol, task, defer
from starpy import fastagi
import logging, time
import logging.config
import json
from pymongo import MongoClient
import txredisapi as redis
#
logger = logging.getLogger('odin_monitor')
#
MIXMONITOR_DIR="/home/vassilux/rc1_test"
#

class RedisSubsProtocol(redis.SubscriberProtocol):
    def connectionMade(self):
        self.subscribe("odin_agi_monitor_request")

    def messageReceived(self, pattern, channel, message):
        logger.debug("Redis : incomming message [ pattern=%s, channel=%s message=%s ]." % (pattern, channel, message) )
        if pattern == "subscribe":
            return
        #
        if channel == 'odin_agi_monitor_request':
            self.factory.process_agi_request(message)
        else :
            data = json.loads(message)
            logger.info("Redis : the message type  %s ignored." %(data['id']))



    def connectionLost(self, reason):
        logger.debug("Redis : lost connection.")


class RedisSubFactory(redis.SubscriberFactory):
    # SubscriberFactory is a wapper for the ReconnectingClientFactory
    maxDelay = 120
    continueTrying = True
    #protocol = RedisSubsProtocol

    def __init__(self, host, port):
        self.host = host
        self.port = port


    def startedConnecting(self, connector):
        print 'Started to connect.'

    def buildProtocol(self, addr):
        logger.debug("Redis : Connected 122222.")
        logger.debug("Redis : Resetting reconnection delay")
        self.resetDelay()
        proto = RedisSubsProtocol()
        proto.factory = self
        self.protocol = proto
        return proto

    def start(self):
        #redis_host  = config.get("redis","redis_host")
        #redis_port  = int(config.get("redis","redis_port"))
        self.connector = reactor.connectTCP(self.host, self.port, self)


    def stop(self):
        # TODO: must check if figure out correct way to close
        self.continueTrying = False
        self.protocol.transport.loseConnection()

    def set_agi_worker(self, incallWorker):
        self.incallWorker = incallWorker

    def process_agi_request(self, data):
        if self.incallWorker != None:
            self.incallWorker.process_agi_request(data)
        else:
            logger.error("Redis : RedisSubFactory can't got the amiworker instance")

    def process_action(self, action):
        pass

class MonitorStarter( object ):
	""" Incomming calls """
	def __init__( self, application, agi ):
		"""Store the AGI instance for later usage """
		self.application = application
		self.agi = agi 

	def start( self ):
		"""Begin the dial-plan-like operations"""
		channel = self.agi.variables['agi_channel']
		file='''%s/%s ''' % (MIXMONITOR_DIR, channel)
		'''seq = fastagi.InSequence( )
		seq.append( self.agi.wait, 1 )
		seq.append( self.agi.streamFile, 'hello-world' )		
		seq.append( self.agi.setVariable, 'MONITOR_CALL_FILE_NAME', file)
		seq.append( self.agi.finish, )
		'''
		logger.debug("DialPlan : Answer a new incomming call for channel [%s]", channel)
		return self.agi.setVariable('MONITOR_CALL_FILE_NAME', file).addCallbacks(self.onSetMonitorFile, self.onSetMonitorFileFailure)
		#return self.agi.answer().addCallbacks( self.onAnswered, self.answerFailure )

	def onSetMonitorFile(self, result):
		priority = 999 #int(self.agi.variables['agi_priority']) + 999
		logger.warn( 
			"""SetPriority : %d""", 
			priority
		)
		return self.agi.setPriority(priority).addCallbacks(self.onSetPriority, self.onSetPriorityFailure)
		#df = self.agi.streamFile( 'hello-world' )
		#return df.addCallback( self.onPlayFinished )

	def onSetPriority(self, result):
		logger.warn( 
			"""onSetPriority to onSetPriorityFailure channel %r: %s""", 
			self.agi.variables['agi_channel'], result,
		)
		return self.agi.finish()

	def onSetPriorityFailure(self, reason):
		logger.warn( 
			"""Unable to onSetPriorityFailure channel %r: %s""", 
			self.agi.variables['agi_channel'], reason.getTraceback(),
		)
		return self.agi.finish()

	def onSetMonitorFileFailure(self, raison):
		logger.warn( 
			"""Unable to set MONITOR_CALL_FILE_NAME variable  channel %r: %s""", 
			self.agi.variables['agi_channel'], reason.getTraceback(),
		)
		return self.agi.finish()

	def answerFailure( self, reason ):
		"""Deal with a failure to answer"""
		logger.warn( 
			"""Unable to answer channel %r: %s""", 
			self.agi.variables['agi_channel'], reason.getTraceback(),
		)
		return self.agi.finish()

	def onAnswered( self, resultLine ):
		"""We've managed to answer the channel, yay!"""
		df = self.agi.streamFile( 'hello-world' )
		return df.addCallback( self.onPlayFinished )

	def onPlayFinished(self, result):
		channel = self.agi.variables['agi_channel']
		logger.debug("MonitorAGiFactory : PlayFinished for the channel [%s]."%(channel))
		return self.agi.finish()

	def __removeFromApplication(self):
		''' '''
		channel = self.agi.variables['agi_channel']
		self.application.removeDialPlan(channel)
		return self.agi.finish()

class MonitorFinisher( object ):
	""" Incomming calls """
	def __init__( self, application, agi ):
		"""Store the AGI instance for later usage """
		self.application = application
		self.agi = agi 

	def start( self ):
		"""Begin the dial-plan-like operations"""
		logger.debug("RecordStateChecker : Check monitor state for channel [%s]", self.agi.variables['agi_channel'])
		return self.agi.wait( 2.0 ).addCallback( self.onWaited )
	
	def onWaited( self, result ):
		"""We've finished waiting, tell the user the number"""
		channel = self.agi.variables['agi_channel']
		logger.debug("RecordStateChecker : onWaited on channel finished%r."%(self.agi.variables['agi_channel']))
		return self.agi.finish()

	def onStopMonitorComplete():
		return self.agi.finish()	

	def __removeFromApplication(self):
		''' '''
		channel = self.agi.variables['agi_channel']
		self.application.removeDialPlan(channel)
		return self.agi.finish()



class MonitorApplication(object):
	"""docstring for MonitorApplication"""	
	def __init__(self):
		self.count = 0
		self.inCalls = {}
		logger.debug("MonitorApplication : init.")
		#self.mongoConn = yield txmongo.MongoConnection(mongo_host, mongo_port)
		#self.mongoColl = self.mongoColl.odin.monitor

	@defer.inlineCallbacks
	def connectToMongt(self):
		#self.mongoConn = yield txmongo.MongoConnection(mongo_host, mongo_port)
		pass


	def __call__(self, agi):
		channel = agi.variables['agi_channel']
		logger.debug("MonitorApplication : Incomming call for the channel [%s] comming.", channel)
		extension = agi.variables['agi_extension']
		logger.debug("MonitorApplication : Incomming call for the extension [%s] comming.", extension)
		if extension == 'h':
			logger.debug("MonitorApplication : Incomming call for the channel [%s] comming.", channel)
			dp = MonitorFinisher(self,agi)
			df = dp.start()
		else:
			self.count = self.count + 1
			dp = MonitorStarter(self, agi)		
			self.inCalls[channel] = dp
			df = dp.start()
			logger.debug("MonitorApplication : RecordStarter started for the channel [%s].", channel)
			return df


	def removeDialPlan(self, channel):
		if self.inCalls.has_key(channel):
			del self.inCalls[channel]
			self.count = self.count - 1
			logger.warn("MonitorApplication : Incomming call for the channel [%s] removed.", channel)
		else:
			logger.warn("MonitorApplication : Can't find an incomming call for the channel [%s].", channel)
		

class MonitorAGiFactory(fastagi.FastAGIFactory):
	"""docstring for ClassName"""
	def __init__(self, dialplan, redis_host, redis_port):
		fastagi.FastAGIFactory.__init__(self, dialplan)
		self.lc = task.LoopingCall(self.check_calls)
		self.lc.start(10)
		self._redisFactory = RedisSubFactory(redis_host, redis_port)
		self._redisFactory.set_agi_worker(self)
		self._redisFactory.start()
		fastagi.log.setLevel( logging.DEBUG )

	def check_calls(self):
		#logger.debug( 'check_calls' )
		pass

	def process_agi_request(self, data):
		logger.debug("MonitorAGiFactory : Get request from odin server.")
		request = json.loads(data)
		requestId = request['id']
		if requestId == None:
			logger.error("MonitorAGiFactory : Can not find request id, the request ignored.")
		else:
			logger.info("MonitorAGiFactory : I'm processing request : %s" % (requestId))
        	if requestId == "commutincall" :
        		reactor.callWhenRunning(self.mainFunction.commutCall, request)
        	else:
        		logger.error("MonitorAGiFactory : Can't find the request handler %s" %(requestId))

'''
class MonitorStrategy(object):
	"""docstring for MonitorStrategy"""
	def __init__(self):
		pass

	def on_start_call(self):
		channel = self.agi.variables['agi_channel']
		logger.debug("MonitorStrategy : on_start_call channel=%s." % (channel) )

	def on_hangup_call(self):
		channel = self.agi.variables['agi_channel']
		logger.debug("MonitorStrategy : on_hangup_call channel=%s." % (channel) )
		pass

		

class MyMonitorApplication(UtilApplication):
	"""docstring for MonitorApplication"""
	def __init__(self):
		self.configFiles = ['/home/vassilux/Projects/odin/config/odinmonitor.conf']
		print 'UtilApplication'
		UtilApplication.__init__(self)

'''		
