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
import sys, warnings
import struct
import logging
import logging.config
from commons import BasicObject, BasicObjectEncoder, OdinConfigParser
from ConfigParser import NoOptionError


#Initialise logger from the configuration file , each part of the applicaiton ami and f1com server has a own logger configuration
logging.config.fileConfig(os.path.join(sys.path[0],'../conf/odinamilogger.conf'))
#
logger = logging.getLogger("odin_f1com");
#Dump object logging hard coded :-)
logging.DUMPOBJECTS = False

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
    print "You need twisted matrix 10.1+ to run F1COMWORKER. Get it from http://twistedmatrix.com/"
    sys.exit(1)

try:
    import txredisapi as redis
except Exception, e:
    print "PYF1COM ERROR: Module txredisapi not found."

try:
    from f1com import AMIBridge, F1ComFactory
except Exception, e:
    print "PYF1COM ERROR: Module F1COMWORKER not found."
    sys.exit(1)

try:
    import json
except ImportError:
    print "PYF1COM ERROR: Can't import json."
    sys.exit(1)

#
config = OdinConfigParser()
#

#f = logfile.LogFile("simplesrv.log", "/tmp", rotateLength=100000)
class RedisSubsProtocol(redis.SubscriberProtocol):
    def connectionMade(self):
        self.subscribe("odin_ami_data_channel")

    def messageReceived(self, pattern, channel, message):
        logger.debug("Redis : incomming message [ pattern=%s, channel=%s message=%s ]." % (pattern, channel, message) )
        if pattern == "subscribe":
            return
        #
        if channel == 'odin_ami_data_channel':
            self.factory.process_ami_data(message)
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
        self.connector = reactor.connectTCP(self.host, self.port, self)

    def stop(self):
        # TODO: must check if figure out correct way to close
        self.continueTrying = False
        self.protocol.transport.loseConnection()

    def set_ami_worker(self,f1comworker):
        self.f1comworker = f1comworker

    def process_ami_data(self, data):
        if self.f1comworker != None:
            self.f1comworker.process_ami_data(data)
        else:
            logger.error("Redis : RedisSubFactory can't got the F1COMWORKER instance")

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

#

##
## Main
##
def run_f1com_srv():
    #
    config_file = os.path.join(sys.path[0],'../conf/odinf1com.conf')
    config.read(config_file)
    #default values initialized butn nod used. I kill process can be better that run with default
    redis_host = "localhost"
    redis_port = 6379
    f1com_port = 3002
    try:
        redis_host  = config.get("redis","redis_host")
        redis_port  = int(config.get("redis","redis_port"))
    except NoOptionError:
        logger.error("F1COM : Parameter redis_host or  redis_port missing. \
            Please check the configuration file odinf1com.conf. Value redis_host or  redis_port missing from the section redis.")
        reactor.stop()
    #
    try:
        f1com_port  = int(config.get("f1com","f1com_bind_port"))
    except NoOptionError:
        logger.error("F1COM : Parameter f1com_bind_port missing. \
            Please check the configuration file odinf1com.conf. Value f1com_bind_port missing from the section f1com.")
        reactor.stop()
    #
    redisSubsFactory = RedisSubFactory(redis_host, redis_port);
    redisSubsFactory.start()
    redisPublisher = OdinRedisPublisher(redis_host, redis_port)
    redisPublisher.start()
    amiBridge = AMIBridge(config, redisPublisher)
    redisSubsFactory.set_ami_worker(amiBridge)
    factory = F1ComFactory()
    factory.set_ami_worker(amiBridge)
    amiBridge.set_f1com_factory(factory)
    reactor.listenTCP(f1com_port,factory)
    #
    def customHandler(signum, stackframe):
        logger.info("run_srv : customHandler got signal : %s." % signum )
        amiBridge.stop()
        redisSubsFactory.stop()
        reactor.callFromThread(reactor.stop) # to stop twisted code when in the reactor loop
    #install signal handler 
    signal.signal(signal.SIGINT, customHandler)
    #


if __name__ == '__main__':
    reactor.callWhenRunning(run_f1com_srv)
    reactor.run()
    logger.info("Reactor stopped. Bye.")    