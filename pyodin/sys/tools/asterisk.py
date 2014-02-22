#
#
#
#

import sys
import os
import socket
import fcntl
import struct
import subprocess

#asterisk bin place
ASTERISK_BIN="/usr/sbin/asterisk"


def _run_asterisk_command(command):
	pipe = subprocess.Popen(['/usr/sbin/asterisk', '-nrx', command], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	result = pipe.communicate()[0]
	try:
		pipe.terminate()
	except:
		pass
		return result

def get_asterisk_version():	
	result = _run_asterisk_command("core show version")
	version = result.split(" ")[1]
	return version

def get_asterisk_times():	
	result = _run_asterisk_command("core show uptime")
	uptime="0"
	reloadtime = "0"
	try:
		uptime = result.split("\n")[0].split(":")[1]
		reloadtime = result.split("\n")[1].split(":")[1]
	except Exception, e:
		pass
	else:
		pass
	finally:
		pass
	
	info = {}
	info['uptime'] = uptime
	info['reloadtime'] = reloadtime
	return info

def get_asterisk_active_channels():
	pass

def get_asterisk_calls():
	result = _run_asterisk_command("core show calls")
	active="-1"
	processed="-1"
	try:
		active = result.split("\n")[0].split(" ")[0]
		processed = result.split("\n")[1].split(" ")[0]
	except Exception, e:
		pass
	else:
		pass
	finally:
		pass	
	info = {}
	info['active'] = active
	info['processed'] = processed
	return info
