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
from fastagi import MonitorAGiFactory, MonitorApplication


#Initialise logger from the configuration file , each part of the applicaiton ami and f1com server has a own logger configuration
logging.config.fileConfig(os.path.join(sys.path[0],'../conf/odinamilogger.conf'))
#
logger = logging.getLogger("odin_monitor");
#Dump object logging hard coded :-)
logging.DUMPOBJECTS = True

try:
    from twisted.internet import reactor
except ImportError:
    print "MONITORFASTAGI: Module twisted not found."
    print "You need twisted matrix 10.1+ to run MONITORFASTAGI. Get it from http://twistedmatrix.com/"
    sys.exit(1)

try:
    import txredisapi as redis
except Exception, e:
    print "MONITORFASTAGI ERROR: Module txredisapi not found."
    sys.exit(1)

try:
    from fastagi import IncallAGiFactory, IncallApplication
except Exception, e:
    print "MONITORFASTAGI ERROR: Module IncallAGiFactory not found."
    sys.exit(1)

#
config = OdinConfigParser()
#

def testFunction( agi ):
	"""Demonstrate simplistic use of the AGI interface with sequence of actions"""
	log.debug( 'testFunction' )
	def setX( ):
		return agi.setVariable( 'this"toset', 'That"2set' )
	def getX( result ):
		return agi.getVariable( 'this"toset' )
	def onX( value ):
		print 'Retrieved value', value 
		reactor.stop()
	return setX().addCallback( getX ).addCallbacks( onX, onX )

def run_fast_srv():
	config_file = os.path.join(sys.path[0],'../conf/odinmonitor.conf')
	config.read(config_file)
	fastagi_port = int(config.get("fastagi","port"))
	fastagi_addr = config.get("fastagi", "address")
	redis_host  = config.get("redis","redis_host")
	redis_port  = int(config.get("redis","redis_port"))
	logger.debug("MonitorAGiFactory : Starting fastagi server on %s:%d." % (fastagi_addr, fastagi_port))
	f = MonitorAGiFactory(MonitorApplication(config), redis_host, redis_port)
	reactor.listenTCP(fastagi_port, f, 50, fastagi_addr)

if __name__ == "__main__":
	#so far so good 
	reactor.callWhenRunning(run_fast_srv)
	reactor.run()
'''
	logging.basicConfig()
	fastagi.log.setLevel( logging.DEBUG )
	#monitorStrategy = MonitorStrategy()
	APPLICATION = MyMonitorApplication()
	APPLICATION.handleCallsFor( 's', testFunction)
	#APPLICATION.handleCallsFor( 'h', monitorStrategy.on_hangup_call)
	APPLICATION.agiSpecifier.run( APPLICATION.dispatchIncomingCall )
	print 'start'
	reactor.run()
'''