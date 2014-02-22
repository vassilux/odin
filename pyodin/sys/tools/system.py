#
# System information functions, i little helpt for pcutil
#
import sys
import os
import socket
import fcntl
import struct
import subprocess

import psutil
from psutil._compat import print_

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    addr = ''
    try:
    	addr = socket.inet_ntoa(fcntl.ioctl(s.fileno(),
    	                                    0x8915,  # SIOCGIFADDR
    	                                    struct.pack('256s', ifname[:15])
    	                                    )[20:24])
    except Exception, e:
    	pass
    else:
    	pass
    finally:
    	pass
    return addr

def bytes2human(n):
    # http://code.activestate.com/recipes/578019
    # >>> bytes2human(10000)
    # '9.8K'
    # >>> bytes2human(100001221)
    # '95.4M'
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i+1)*10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.1f%s' % (value, s)
    return "%sB" % n

def get_ntuple(nt):
	values = {}
	for name in nt._fields:
		value = getattr(nt, name)
		if name != 'percent':
			value = bytes2human(value)
			values[name.lower()]=value
	#
	return values


def disk_usage():
	disks = []
	for part in psutil.disk_partitions(all=False):
		usage = psutil.disk_usage(part.mountpoint)
		disk = {}
		disk['mount'] = part.mountpoint
		disk['device'] = part.device
		disk['total'] = bytes2human(usage.total)
		disk['used'] = bytes2human(usage.used)
		disk['free'] = bytes2human(usage.free)
		disk['precent'] = str(int(usage.percent)) + '%'
		disk['type'] = part.fstype
		disks.append(disk)
	#
	return disks

def memory_usage():
	memory = {}
	res = psutil.virtual_memory()
	memory['virtual'] = get_ntuple(psutil.virtual_memory())
	memory['swap'] = get_ntuple(psutil.swap_memory())
	return memory

def nic_inf():
	net = psutil.net_io_counters(True)
	infs = []
	for inf in net:
		interface = {}
		interface['name']=inf
		interface['data'] = get_ntuple(net[inf])
		ip_addr = get_ip_address(inf)
		interface['addr'] = ip_addr
		infs.append(interface)
	#
	return infs

def system_time():
	systime = {}
	pipe = subprocess.Popen(["uptime"], stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	upt = pipe.communicate()[0].split()
	pipe.wait()
	pipe = subprocess.Popen(["date"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	systime['systime'] = pipe.communicate()[0]
	pipe.wait()
	systime['uptime'] = "%s %s" % (upt[2], upt[3].rstrip(','))
	return systime

def get_hostname():
	pipe = subprocess.Popen(["/bin/hostname"], stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	hostname = pipe.communicate()[0]
	hostname = hostname.strip()
	return hostname