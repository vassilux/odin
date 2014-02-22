#! /usr/bin/env python
'''
check how test 
'''
import sys
import os
sys.path.append(os.path.join(sys.path[0],'../'))
sys.path.append(os.path.join(sys.path[0],'../sys'))

import logging
import logging.config
import socket
import fcntl
import struct
import subprocess

from commons import OdinConfigParser

from tools import *

logging.config.fileConfig(os.path.join(sys.path[0],'../conf/odinsyslogger.conf'))
logger = logging.getLogger("odin_sys");

try:
    from twisted.python import failure
    from twisted.internet import reactor, task, defer
    from twisted.internet import error as tw_error
    from twisted.web import resource
    from twisted.protocols import basic
    from twisted.internet import protocol
    from twisted.application import service, internet
    from twisted.internet import threads
except ImportError:
    print "ODINSYSMON ERROR: Module twisted not found."
    print "You need twisted matrix 10.1+ to run ODINSYSMON. Get it from http://twistedmatrix.com/"
    sys.exit(1)

config = OdinConfigParser()

def main():
    config_file = os.path.join(sys.path[0],'../conf/odinsys.conf')
    config.read(config_file)
    factory = protocol.ServerFactory()
    factory.protocol = OdinSysInfoProtocol
    factory.clients = []
    #
    port = int(config.get("global","bind_port"))
    reactor.listenTCP(port,factory)
    logger.debug("ODINSYS : Server started and listen on the port : %i" %(port))
    reactor.run()

if __name__ == '__main__':
	main()
