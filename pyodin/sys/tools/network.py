#
#
#
#

import sys
import os
import logging
import logging.config
import socket
import fcntl
import struct
import subprocess

from tools import *

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

try:
	import json
except ImportError:
	print "ODINSYSMON ERROR: Can't import json."
	sys.exit(1)



def collect_informations():
	sysinfo= {}
	sysinfo['hostname'] = get_hostname()
	sysinfo['memory'] = memory_usage()
	sysinfo['disks'] = disk_usage()
	sysinfo['infs'] = nic_inf()
	sysinfo['time'] = system_time()
	#asterisk part of system informations
	sysinfo['asterisk'] = {}
	sysinfo['asterisk']['version'] = get_asterisk_version()
	asterisktimes = get_asterisk_times()
	#asterisk times collected informations 	
	sysinfo['asterisk']['upTime'] = asterisktimes['uptime']
	sysinfo['asterisk']['reloadTime'] = asterisktimes['reloadtime']
	#asterisk calls information
	calls = get_asterisk_calls()
	sysinfo['asterisk']['activeCalls'] = calls['active']
	sysinfo['asterisk']['processedCalls'] = calls['processed']
	return sysinfo

class OdinSysInfoProtocol(basic.LineReceiver):

	def __init__(self):
		self.eventHandlers = {
		'getsysinfo': self.handler_getsysinfo,
		'quit': self.handler_quit
		}

	def connectionMade(self):
		d = self.transport.getPeer()
		logger.debug("ODINSYS  : New client connected from [%s:%s]." % (d.host, d.port))
		self.factory.clients.append(self)

	def connectionLost(self, reason):
		d = self.transport.getPeer()
		logger.info("ODINSYS : Connection lost , I remove myself [%s:%s] from factory." % (d.host, d.port))
		self.factory.clients.remove(self)

	def lineReceived(self, line):
		logger.debug("ODINSYS : New data received : [%s]." %(repr(line)))
		request = json.loads(line)
		request_type = request['type'].encode('utf-8')
		handler = self.eventHandlers.get(request_type)
		if handler:
			handler()
		else:
			response = {}
			response['type']='error'
			response['message']='Can not find message'
			to_json = json.dumps(response)
			self.message(to_json)

	def message(self, message):
		self.transport.write(message + '\n')

	def handler_getsysinfo(self):
		'''
		Handler for the request to get the system informations
		'''
		#add the processe to get the system informations
		d = threads.deferToThread(collect_informations)
		d.addCallback(self.cb_getsysinto)
		

	def handler_quit(self):
		self.transport.loseConnection()

	#worked part
	def cb_getsysinto(self, result):
		response = {}
		response['type']='sysinfo'
		response['message']=result
		to_json = json.dumps(response)
		self.message(to_json)
