#! /usr/bin/env python
import os
import sys
#add the parent path
sys.path.append(os.path.join(sys.path[0],'../'))

import re
import time
import logging
import optparse
import signal
import json
from commons import OdinConfigParser
from ami import OdinAMIFacade
import logging.config
#Initialise logger from the configuration file , each part of the applicaiton ami and f1com server has a own logger configuration
#print "path : %s"%os.path.join(sys.path[0],'../conf/odinamilogger.conf')
logging.config.fileConfig(os.path.join(sys.path[0],'../conf/odinamilogger.conf'))
#Dump object logging hard coded :-)
logging.DUMPOBJECTS = False
logger = logging.getLogger("odin_ami"); 

try:
	from twisted.python import failure
	from twisted.internet import reactor, task, defer
	from twisted.internet import error as tw_error
	from twisted.application import internet
	from twisted.application import service
	from twisted.internet.defer import inlineCallbacks

except ImportError:
	print "AMIWORKER ERROR: Module twisted not found."
	print "You need twisted matrix 10.1+ to run AMIWORKER. Get it from http://twistedmatrix.com/"
	sys.exit(1)

try:
	import txredisapi as redis
except Exception, e:
	print "AMIWORKER ERROR: Module txredisapi not found."

try:
	from ami import OdinAMIFacade
except Exception, e:
	print "AMIWORKER ERROR: Module amidispatcher not found."
	sys.exit(1)

try:
	import json
except ImportError:
	print "AMIWORKER ERROR: Can't import json."
	sys.exit(1)


#
config = OdinConfigParser()
#


class RedisSubsProtocol(redis.SubscriberProtocol):
    def connectionMade(self):
        self.subscribe("odin_ami_action_channel")
        self.subscribe("odin_ami_request_channel")

    def messageReceived(self, pattern, channel, message):
    	logger.debug("Redis : incomming message [ pattern=%s, channel=%s message=%s ]." % (pattern, channel, message) )
    	if pattern == "subscribe":
    		return
    	#
    	if channel == 'odin_ami_action_channel':
    		self.factory.process_action(message)
    	elif channel == 'odin_ami_request_channel':
    		self.factory.process_request(message)
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
        logger.debug("Redis : Connection...")

    def buildProtocol(self, addr):
    	logger.debug("Redis : Connected.")
    	logger.debug("Redis : Resetting reconnection delay")
        self.resetDelay()
        proto = RedisSubsProtocol()
        proto.factory = self
        self.protocol = proto
        return proto

    def start(self):
    	redis_host  = config.get("redis","redis_host")
    	redis_port  = int(config.get("redis","redis_port"))
        self.connector = reactor.connectTCP(self.host, self.port, self)


    def stop(self):
        # TODO : figure out correct way to close
        self.continueTrying = False
        self.protocol.transport.loseConnection()

    def set_ami_worker(self,amiworker):
    	self.amiworker = amiworker

    def process_request(self, request):
    	if self.amiworker != None:
    		self.amiworker.process_request(request)
    	else:
    		logger.error("Redis : RedisSubFactory can't got the amiworker instance")

    def process_action(self, action):
    	pass

class OdinRedisPublisher(object):
	"""docstring for OdinRedisPublisher"""
	def __init__(self, redis_host, redis_port):
		self.redis_host = redis_host
		self.redis_port = redis_port

	def start(self):
		#
		reactor.callWhenRunning(self._start)

	@defer.inlineCallbacks
	def _start(self):
		self.db = yield redis.Connection(self.redis_host, self.redis_port, reconnect=True)

	def stop(self):
		self.db.disconnect()

	def publish(self,channel,message):
		self.db.publish(channel,message)

		
##
## Daemonizer
##
#MONAST_PID_FILE = '%s/.monast.pid' % sys.argv[0].rsplit('/', 1)[0]
AMIWORKER_PID_FILE = '/var/run/odinami.pid'
def createDaemon():
	if os.fork() == 0:
		os.setsid()
		if os.fork() == 0:
			os.chdir(os.getcwd())
			os.umask(0)
		else:
			os._exit(0)
	else:
		os._exit(0)
	
	pid = os.getpid()
	print '\nAMIWORKER daemonized with pid %s' % pid
	f = open(AMIWORKER_PID_FILE, 'w')
	f.write('%s' % pid)
	f.close()


##
## Main
##
def run_srv():
	config_file = os.path.join(sys.path[0],'../conf/odinami.conf')
	config.read(config_file)
	redis_host  = config.get("redis","redis_host")
	redis_port  = int(config.get("redis","redis_port"))
	#
	redisSubsFactory = RedisSubFactory(redis_host, redis_port);
	redisSubsFactory.start()
	redisPublisher = OdinRedisPublisher(redis_host, redis_port)
	redisPublisher.start()
	odinAmiFacade = OdinAMIFacade(config, redisPublisher)
	redisSubsFactory.set_ami_worker(odinAmiFacade)
	#
	def customHandler(signum, stackframe):
		logger.info("run_srv : customHandler got signal : %s." % signum )
		odinAmiFacade.stop()
		redisSubsFactory.stop()
		#db.disconnect()
		reactor.callFromThread(reactor.stop) # to stop twisted code when in the reactor loop
	#install signal handler 
	signal.signal(signal.SIGINT, customHandler)

	#
	

if __name__ == '__main__':
	reactor.callWhenRunning(run_srv)
	reactor.run()
	logger.info("Reactor stopped. Bye.")
	
	
