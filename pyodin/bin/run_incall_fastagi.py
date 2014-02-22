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
from fastagi import IncallAGiFactory, IncallApplication

#Initialise logger from the configuration file , each part of the applicaiton ami and f1com server has a own logger configuration
logging.config.fileConfig(os.path.join(sys.path[0],'../conf/odinamilogger.conf'))
#
logger = logging.getLogger("odin_incall");
#Dump object logging hard coded :-)
logging.DUMPOBJECTS = False

try:
    from twisted.internet import reactor
except ImportError:
    print "INCALLFASTAGI: Module twisted not found."
    print "You need twisted matrix 10.1+ to run INCALLFASTAGI. Get it from http://twistedmatrix.com/"
    sys.exit(1)

try:
    import txredisapi as redis
except Exception, e:
    print "INCALLFASTAGI ERROR: Module txredisapi not found."
    sys.exit(1)

try:
    from fastagi import IncallAGiFactory, IncallApplication
except Exception, e:
    print "INCALLFASTAGI ERROR: Module IncallAGiFactory not found."
    sys.exit(1)

#
config = OdinConfigParser()
#

def run_fast_srv():
	config_file = os.path.join(sys.path[0],'../conf/odinincall.conf')
	config.read(config_file)
	fastagi_port = int(config.get("fastagi","port"))
	fastagi_addr = config.get("fastagi", "address")
	redis_host  = config.get("redis","redis_host")
	redis_port  = int(config.get("redis","redis_port"))
	f = IncallAGiFactory(IncallApplication(), redis_host, redis_port)
	reactor.listenTCP(fastagi_port, f, 50, fastagi_addr)

if __name__ == "__main__":
	#so far so good 
	reactor.callWhenRunning(run_fast_srv)
	reactor.run()
