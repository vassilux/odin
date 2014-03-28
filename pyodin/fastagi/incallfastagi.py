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
from twisted.internet import reactor,protocol, task, defer
from starpy import fastagi
import logging, time
import logging.config
import json
from pymongo import MongoClient
import txredisapi as redis
#
logger = logging.getLogger( 'odin_incall' )


def testFunction( agi ):
	"""Give time for some time a bit in the future"""
	logger.debug( 'testFunction new call' )
	df = agi.streamFile( 'pls-wait-connect-call' )
	def onFailed( reason ):
		logger.error( "Failure: %s", reason.getTraceback())
		return None
	def cleanup( result ):
		agi.finish()
		return result
	def onSaid( resultLine ):
		"""Having introduced, actually read the time"""
		t = time.time()
		t2 = t+5.0
		df = agi.sayDateTime( t2, format='HM' )
		def onDateFinished( resultLine ):
			# now need to sleep until .5 seconds before the time 
			df = agi.wait( t2-.5-time.time() )
			def onDoDialOperator( result ):
				#df = agi.streamFile( 'beep' )
				df = agi.execute( 'Dial', 'SIP/6000' )
				return df
			return df.addCallback( onDoDialOperator )
		return df.addCallback( onDateFinished )
	return df.addCallback( 
		onSaid 
	).addErrback( 
		onFailed 
	).addCallbacks(
		cleanup, cleanup,
	)

class RedisSubsProtocol(redis.SubscriberProtocol):
    def connectionMade(self):
        self.subscribe("odin_agi_request_channel")

    def messageReceived(self, pattern, channel, message):
        logger.debug("Redis : incomming message [ pattern=%s, channel=%s message=%s ]." % (pattern, channel, message) )
        if pattern == "subscribe":
            return
        #
        if channel == 'odin_agi_request_channel':
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
        logger.debug("Redis : Connected.")
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

class DialPlan( object ):
	""" Incomming calls """
	def __init__( self, application, agi ):
		"""Store the AGI instance for later usage """
		self.application = application
		self.agi = agi 

	def start( self ):
		"""Begin the dial-plan-like operations"""
		logger.debug("DialPlan : Answer a new incomming call for channel [%s]", self.agi.variables['agi_channel'])
		return self.agi.answer().addCallbacks( self.onAnswered, self.answerFailure )

	def answerFailure( self, reason ):
		"""Deal with a failure to answer"""
		logger.warn( 
			"""Unable to answer channel %r: %s""", 
			self.agi.variables['agi_channel'], reason.getTraceback(),
		)
		return self.__removeFromApplication()

	def onAnswered( self, resultLine ):
		"""We've managed to answer the channel, yay!"""
		df = self.agi.streamFile( 'pls-wait-connect-call' )
		return df.addCallback( self.onPlayFinished )

	def onPlayFinished(self, result):
		logger.debug("IncallAGiFactory : PlayFinished for the channel [%s]."%(self.agi.variables['agi_channel']))
		return self.agi.wait( 2.0 ).addCallback( self.onWaited )

	def onWaited( self, result ):
		"""We've finished waiting, tell the user the number"""
		logger.debug("IncallAGiFactory : onWaited on channel %r."%(self.agi.variables['agi_channel']))
		channel = self.agi.variables['agi_channel']
		return self.agi.channelStatus( channel).addErrback(
			self.onChannelStatusFailed,
		).addCallbacks(
			self.onChannelStatusFinished, self.onChannelStatusFailed,
		)
	def onChannelStatusFinished( self, result ):
		"""We said the number correctly, hang up on the user"""
		logger.debug("IncallAGiFactory : onChannelStatusFinished on channel [%r] with result [%s]."%(self.agi.variables['agi_channel'], result))
		return self.agi.wait( 2.0 ).addCallback( self.onWaited )

	def onChannelStatusFailed( self, reason ):
		"""We were unable to read the number to the user"""
		logger.debug( 
			"""IncallAGiFactory : onChannelStatusFailed unable to get the channel status %r: %s""",
			self.agi.variables['agi_channel'], reason.getTraceback(),
		)
		return self.__removeFromApplication()

	def onDial(self, reason):
		''' '''
		logger.debug("IncallAGiFactory : onDial finished with result [%s] for the channel [%s]."%(reason, self.agi.variables['agi_channel']))
		#return self.__removeFromApplication()
		df = defer.Deferred()
		reactor.callLater(1.0, df.callback, 0)
		return df
	

	def onDialFailed(self, reason):
		''' '''
		logger.warn( 
			"""Unable to dial channel %r: %s""", 
			self.agi.variables['agi_channel'], reason.getTraceback(),
		)
		return self.__removeFromApplication()
		
	def onHangupFailure( self, reason ):
		"""Failed trying to hang up"""
		logger.warn( 
			"""Unable to hang up channel %r: %s""", 
			self.agi.variables['agi_channel'], reason.getTraceback(),
		)


	def commutCall(self, request):
		''' Communt incomming call to the operator '''
		post = request['post']
		df = self.agi.execute( 'Dial', 'SIP/' + post ).addErrback(self.onDialFailed,
			).addCallbacks(
				self.onDial, self.onDialFailed,
			)

	def __removeFromApplication(self):
		''' '''
		channel = self.agi.variables['agi_channel']
		self.application.removeDialPlan(channel)
		return self.agi.finish()

class MongoAdapter(object):
	"""docstring for MongoAdapter"""
	def __init__(self, host, port):
		super(MongoAdapter, self).__init__()
		self.host = host
		self.port = port

	def connect(self):
		self._client = MongoClient(self.host, self.port)
		
class IncallApplication(object):
	"""docstring for IncallApplication"""	
	def __init__(self):
		self.count = 0
		self.inCalls = {}

	def __call__(self, agi):
		channel = agi.variables['agi_channel']
		logger.debug("IncallApplication : Incomming call for the channel [%s] comming.", channel)
		self.count = self.count + 1
		dp = DialPlan(self, agi)		
		self.inCalls[channel] = dp
		df = dp.start()
		logger.debug("IncallApplication : DialPlan started for the channel [%s].", channel)
		return df

	def commutCall(self, request):
		channel = request['channel']
		if channel:
			dp = self.inCalls[channel]
			dp.commutCall(request)

	def removeDialPlan(self, channel):
		if self.inCalls.has_key(channel):
			del self.inCalls[channel]
			self.count = self.count - 1
			logger.warn("IncallApplication : Incomming call for the channel [%s] removed.", channel)
		else:
			logger.warn("IncallApplication : Can't find an incomming call for the channel [%s].", channel)
		

class IncallAGiFactory(fastagi.FastAGIFactory):
	"""docstring for ClassName"""
	def __init__(self, dialplan, redis_host, redis_port):
		fastagi.FastAGIFactory.__init__(self, dialplan)
		self.mongoAdapter = MongoAdapter("localhost",27017)
		self.mongoAdapter.connect()
		self.lc = task.LoopingCall(self.check_calls)
		self.lc.start(10)
		self._redisFactory = RedisSubFactory(redis_host, redis_port)
		self._redisFactory.set_agi_worker(self)
		self._redisFactory.start()

	def check_calls(self):
		#logger.debug( 'check_calls' )
		pass

	def process_agi_request(self, data):
		logger.debug("IncallAGiFactory : Get request from odin server.")
		request = json.loads(data)
		requestId = request['id']
		if requestId == None:
			logger.error("IncallAGiFactory : Can not find request id, the request ignored.")
		else:
			logger.info("IncallAGiFactory : I'm processing request : %s" % (requestId))
        	if requestId == "commutincall" :
        		reactor.callWhenRunning(self.mainFunction.commutCall, request)
        	else:
        		logger.error("IncallAGiFactory : Can't find the request handler %s" %(requestId))


'''		
if __name__ == "__main__":
	#logging.basicConfig()
	fastagi.log.setLevel( logging.DEBUG )
	f = IncallAGiFactory(IncallApplication())
	reactor.listenTCP(4575, f, 50, '127.0.0.1') # only binding on local interface
	reactor.run()
'''