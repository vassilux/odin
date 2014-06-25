#! /usr/bin/env python
'''
The agi script works with  the dialplan macro [macro-record-enable]
Set the variable  MIXMON_DIR into the globals section of the extentions.conf file : something like /data/audio/
Channel variable MONITOR_CALL_FILE_NAME initialized by agi script and used by macro to start monitor for given channel.
Extention 999 used by agi to go vers start monitor into macro-record-enable
Redis channel odin_ami_data_channel used for communicaiton with f1com driver or other system to notificaitons

'''
import os
import sys
from twisted.internet import reactor,protocol, task, defer
from starpy import fastagi
import logging, time
import logging.config
import json
import txredisapi as redis
import json

try:
    from twisted.enterprise import adbapi
except ImportError:
    print "MONITORFASTAGI :: Can't import twisted.enterprise."
    sys.exit(1)
'''try:
    from twistar.registry import Registry
    from twistar.dbobject import DBObject
except ImportError:
    print "MONITORFASTAGI :: Can't import twistar."
    sys.exit(1)
'''
#
logger = logging.getLogger('odin_monitor')
#
MIXMONITOR_DIR="/home/rc1"
#the priority to jump into macro-record-enable
MACRO_RECORD_PRIORITY=999
#
REDIS_NOTIFICATION_CHANNEL='odin_ami_data_channel'
		

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
            logger.error("Redis : RedisSubFactory can't get the amiworker instance")

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

class WaveCopyProtocol(protocol.ProcessProtocol):
	def __init__(self, src, dst):
		self.src = 	src
		self.dst = dst

	def outReceived(self, data):
		logger.debug("WaveCopyProtocol : [%s]."%(data))

	def processEnded(self, reason):
		if reason.value.exitCode == 0:
			logger.debug("WaveCopyProtocol :: Try to convert the file [%s]  to a-law file [%s]"%(self.dst, self.src))
			convert_args = "%s %s %s"%(self.dst,"-r 8000 -b 8 -c 1 -e a-law",self.src)
			logger.error("WaveConvertProtocol :: convert_args [%s]." %(convert_args))
			waveConvertProto = WaveConvertProtocol(self.dst)
			reactor.spawnProcess(waveConvertProto, 'sox', args=['sox',convert_args])
		else:
			logger.error("WaveConvertProtocol :: Failed to copy the file [%s] with reason : [%d]" %(self.src,reason.value.exitCode))

class WaveConvertProtocol(protocol.ProcessProtocol):
	def __init__(self, src):
		self.src = 	src

	def outReceived(self, data):
		logger.debug("WaveConvertProtocol : [%s]."%(data))

	def processEnded(self, reason):
		if reason.value.exitCode == 0:
			logger.debug("WaveConvertProtocol :: Try to remove the file [%s]."%(self.src))
			
		else:
			logger.error("WaveConvertProtocol : Failed copy the file [%s] with reason : [%d]" %(self.src,reason.value.exitCode))

		cmd_args = "-f %s"%(self.src)
		waveDeleteProto = WaveDeleteProtocol(self.src)
		logger.error( 
			"""WaveConvertProtocol :: Try to remove the file [%s].""", 
			self.src,
		)
		reactor.spawnProcess(waveDeleteProto, 'rm', args=['rm', cmd_args])


class WaveDeleteProtocol(protocol.ProcessProtocol):
	def __init__(self, src):
		self.src = 	src

	def outReceived(self, data):
		logger.debug("WaveDeleteProtocol : [%s]."%(data))

	def processEnded(self, reason):
		if reason.value.exitCode == 0:
			logger.debug("WaveDeleteProtocol: File [%s] deleted."%(self.src))
		else:
			logger.error("WaveDeleteProtocol : Failed to delete the file [%s] with reason : [%d]" %(self.src,reason.value.exitCode))



class RecordStrategy(object):
	"""docstring for RecordStrategy"""
	def __init__(self):
		super(RecordStrategy).__init__()
		self.arg = arg

	def can_be_register(callerid, extension):
		must_be_register = False
		if callerid == '9002' or extension == '1157':
			must_be_register = True
		return must_be_register


class MonitorStarting( object ):
	""" Incomming calls """
	def __init__( self, application, agi ):
		"""Store the AGI instance for later usage """
		self.application = application
		self.agi = agi
		self._recordAll = False 


	def start( self ):
		"""Begin the dial-plan-like operations"""
		value='RECORD_ALL'
		return self.application.get_dbpool().runQuery("SELECT value FROM settings WHERE variable LIKE '%s'"%(value)).addCallbacks(self.on_done_recorde_value, self.on_done_recorde_value_failure)

	def on_done_recorde_value(self, result):
		logger.debug("MonitorStarting :: Recording object from the database [%s]", result)
		channel = self.agi.variables['agi_channel']
		if result != None :
			self._recordAll = result[0][0]
			logger.debug("MonitorStarting :: init self._recordAll  [%s]", self._recordAll)
		else:
			logger.debug("MonitorStarting :: Recording skipped for the channel on_done_recorde_value value None [%s]", channel)
			return self.agi.finish()
		#
		if self._recordAll == 'True':
			fileid = self.agi.variables['agi_uniqueid'].replace('.','')
			self.monitor_file="%s.wav" % (fileid)
			return self.agi.setVariable('MONITOR_CALL_FILE_NAME', self.monitor_file).addCallbacks(self.on_set_monitor_file, self.on_set_monitor_fileFailure)
		else:
			logger.debug("MonitorStarting :: self._recordAll initialized [%s]", self._recordAll)
			dnid = self.agi.variables['agi_dnid'][-4:]
			cid = self.agi.variables['agi_callerid']
			sql = "SELECT * FROM rc1.recordNumbers WHERE number LIKE '%s' OR number LIKE '%s'"%(dnid, cid)
			logger.debug("MonitorStarting :: Sql query for did [%s]", sql)
			return self.application.get_dbpool().runQuery(sql).addCallbacks(self.on_done_did_callerid, self.on_done_did_callerid_failure)
		

	def on_done_recorde_value_failure(self, reason):
		channel = self.agi.variables['agi_channel']
		logger.debug("MonitorStarting :: Failure get parameter RECORD_ALL with cause [%s] for the channel [%s]", reason, channel)
		return self.agi.finish()

	def on_done_did_callerid(self, result):
		fileid = self.agi.variables['agi_uniqueid'].replace('.','')
		if result == None:
			return self.agi.finish()
		#
		do_record = False
		for number in result:
			logger.debug("MonitorStarting :: on_done_did_callerid check  number [%r] and number3[%r]", number, number[3])
			#
			if number[3] == 0:
				logger.debug("MonitorStarting :: Skip record for heck number [%r] and number3[%r]", number, number[3])
				return self.agi.finish()
			if number[3] == 1:
				do_record = True
				break;
		#
		if do_record == False:
			logger.debug("MonitorStarting :: do_record is [%s] and self._recordAll [%s], the record skipping", do_record, self._recordAll)
			return self.agi.finish()
		#so far so good try record
		self.monitor_file="%s.wav" % (fileid)
		return self.agi.setVariable('MONITOR_CALL_FILE_NAME', self.monitor_file).addCallbacks(self.on_set_monitor_file, self.on_set_monitor_fileFailure)

	def on_done_did_callerid_failure(self, reason):
		dnid = self.agi.variables['agi_dnid'][-4:]
		cid = self.agi.variables['agi_callerid']
		channel = self.agi.variables['agi_channel']
		logger.warning("MonitorStarting :: Failure get recording configuration for DID [%s] and CID [%s] with reason [%s] on the channel [%s].", dnid, cid, reason, channel)
		return self.agi.finish()


	def on_set_monitor_file(self, result):
		"""Insert a record to the rc1 Histroique database table"""
		dnid = self.agi.variables['agi_dnid'][-4:]
		query= "INSERT INTO rc1.Historique (NoTrans, Start, Stop, FileName, StartLong, Duration, CallerID, SDA, F1, XISDN) \
			VALUES ('asterisk_1', Now(), Now(), '%s', 0, '0', '%s', '%s', '1', '1')" % (self.monitor_file, self.agi.variables['agi_callerid'], dnid)
		#
		return self.application.get_dbpool().runQuery(query).addCallbacks(self.on_done_insert_histo, self.on_done_insert_histo_failure)

	def on_done_insert_histo(self, result):
		"""Change the dialplan priority to 999, used in the macro"""
		priority = MACRO_RECORD_PRIORITY
		return self.agi.setPriority(priority).addCallbacks(self.on_set_priority, self.on_set_priority_failure)

	def on_done_insert_histo_failure(self, reason):
		logger.error("MonitorStarting :: Unable to insert the new record into the table Historique for channel %r cause : %s", self.agi.variables['agi_channel'], reason.getTraceback())
		return self.agi.finish()

	def on_set_priority(self, result):
		'''send the start recording call message '''
		message = self.application.build_message('RecordStart', self.monitor_file, self.agi.variables['agi_callerid'])
		self.application.send_record_message(message)
		return self.agi.finish()

	def on_set_priority_failure(self, reason):
		logger.warn( 
			"""Unable to set priority for channel %r: %s""", 
			self.agi.variables['agi_channel'], reason.getTraceback(),
		)
		return self.agi.finish()

	def on_set_monitor_fileFailure(self, raison):
		logger.warn( 
			"""Unable to set MONITOR_CALL_FILE_NAME variable  channel %r: %s""", 
			self.agi.variables['agi_channel'], reason.getTraceback(),
		)
		return self.agi.finish()



class MonitorEnding( object ):
	""" Incomming calls """
	def __init__( self, application, agi ):
		"""Store the AGI instance for later usage """
		self.application = application
		self.agi = agi 

	def start( self ):
		"""Begin the dial-plan-like operations"""
		logger.debug("RecordStateChecker : Check monitor state for channel [%s]", self.agi.variables['agi_channel'])
		return self.agi.getVariable('MONITOR_CALL_FILE_NAME').addCallbacks( self.on_get_monotor_variable, self.on_get_monotor_variable_failure)
	
	def on_get_monotor_variable( self, result ):
		"""Get the value of the MONITOR_CALL_FILE_NAME variable"""
		channel = self.agi.variables['agi_channel']
		if result == None or result == '':
			return self.agi.finish()
		#
		self.monitor_file = result
		return self.agi.setVariable('CDR(recordfile)', self.monitor_file).addCallbacks(self.on_set_cdr_record_file, self.on_set_cdr_record_file_failure)
		
	def on_set_cdr_record_file(self, result):
		return self.agi.getVariable('CDR(billsec)').addCallbacks( self.on_get_duration, self.on_get_duration_failure)

	def on_set_cdr_record_file_failure(self, reason):
		logger.error( 
			"""MonitorEnding :: Failure to set the cdr recordfile field for the channel [%s] with reason [%r].""", 
			self.agi.variables['agi_channel'], reason.getTraceback(),
		)

	def on_get_duration(self, result):
		"""Update a record into the rc1 database for the call duration and the end timestamp."""
		"""CDR field billsec used as the duration value."""
		dnid = self.agi.variables['agi_dnid'][-4:]
		#DATE_FORMAT(Now(),'%%d/%%m/%%Y %%H:%%i:%%s')
		query= "UPDATE rc1.Historique SET Stop = Now(), Duration='%s' WHERE FileName='%s' AND CallerID='%s' AND SDA='%s'" % (result, self.monitor_file, self.agi.variables['agi_callerid'], dnid)
		#
		logger.debug("MonitorEnding : on_get_monotor_variable on channel finished [%r] with duration [%ss]."%(self.agi.variables['agi_channel'],result))
		return self.application.get_dbpool().runQuery(query).addCallbacks(self.on_done_update_histo, self.on_done_update_histo_failure)

	def on_get_duration_failure(self, reason):
		"""Failure to get the duration from CDR. Finish the agi."""
		logger.error( 
			"""MonitorEnding :: Failure to get the call duration for the channel [%s] with reason [%r].""", 
			self.agi.variables['agi_channel'], reason.getTraceback(),
		)
		return self.agi.finish()

	def on_done_update_histo(self, result):
		"""Send the notification message to the redis channel."""
		message = self.application.build_message('RecordEnd', self.monitor_file, self.agi.variables['agi_callerid'])
		#self.application.send_record_message(message)
		
		'''src = "%s%s"%("/home/rc1/", self.monitor_file)
		dst = "%s%s.wav"%("/home/rc1/", self.monitor_file)
		waveCopyProto = WaveCopyProtocol(src, dst)
		logger.error( 
			"""MonitorEnding :: Try copy file [%s] to [%r].""", 
			src, dst,
		)
		reactor.spawnProcess(waveCopyProto, 'cp', args=['cp', src,dst])'''
		return self.agi.finish()

	def on_done_update_histo_failure(self, reason):
		logger.error( 
			"""MonitorEnding :: Failure udpate a record into rc1 historique table for the channel [%s] with reason [%r].""", 
			self.agi.variables['agi_channel'], reason.getTraceback(),
		)
		return self.agi.finish()

	def on_get_monotor_variable_failure( self, raison ):
		return self.agi.finish()

class MonitorApplication(object):
	"""Application bridge to register call.Provides 2 types of dialplan loginc base into extentions."""	
	def __init__(self, config):
		self.config = config
		try:
		    self.asterisk_server = config.get("global", "asterisk")
		    self.site_id = config.get("global", "site_id")
		    self.id_char = config.get("global", "id_char")
		except NoOptionError:
		    logger.error("MonitorApplication :: Failure to initialize. Please check parameters asterisk : [%s] site_id: [%s], id_char: [%s]." %(self.asterisk_server, self.site_id , self.id_char))
		    reactor.stop()
		#
		self._dbpool = adbapi.ConnectionPool(config.get("database", "driver"), user=config.get("database", "user"), passwd=config.get("database", "password"), db=config.get("database", "schema"),cp_reconnect=True, cp_good_sql='select * from settings')

	def __call__(self, agi):
		channel = agi.variables['agi_channel']
		extension = agi.variables['agi_extension']
		logger.debug("MonitorApplication :: New call for the channel [%s] and extension [%s].", channel, extension)
		if extension == 'h':
			logger.debug("MonitorApplication :: It is end of the call , initialize the MonitorEnding for the channel [%s] comming.", channel)
			dp = MonitorEnding(self,agi)
			df = dp.start()
		else:
			dp = MonitorStarting(self, agi)		
			df = dp.start()
			logger.debug("MonitorApplication : RecordStarter started for the channel [%s].", channel)
			return df

	def set_monitor_factory(self, factory):
		""" set the factory instance """
		self.factory = factory

	def get_dbpool(self):
		return self._dbpool


	#############################################################################
	# Workers functions                                                         #
	#                                                                           #
	#############################################################################
	def build_message(self, event, file, calleridnum):
		"""Create a json string for given event """
		logger.debug("MonitorApplication :: file argument : [%s].", file)
		#keep the compatibility with current rc1
		filerc1style='%s%s' % (self.id_char,file.replace('.wav',''))
		alarmevent = {'privilege': 'system,all', 'alarm': 'record', 'event': event, 'file': filerc1style, 'calleridnum': calleridnum}
		to_json = {"id": 'alarm', "server": "asterisk_1", "user": "f1comami", 
		    "alarmevent": alarmevent}
		message = json.dumps(to_json)
		return message

	def send_record_message(self, message):
		"""Send the message into redis specialized channel for notify start of the recording process"""
		self.factory.send_record_message(message)
	

class MonitorAGiFactory(fastagi.FastAGIFactory):
	"""Monitor factory provides the possibility to register a call"""
	def __init__(self, dialplan, redis_host, redis_port):
		fastagi.FastAGIFactory.__init__(self, dialplan)
		dialplan.set_monitor_factory(self)
		self._redisFactory = RedisSubFactory(redis_host, redis_port)
		self._redisFactory.set_agi_worker(self)
		self._redisFactory.start()
		self._redisPublisher = OdinRedisPublisher(redis_host, redis_port)
		self._redisPublisher.start()

	def send_record_message(self, message):
		"""Publish the given message tho the redis channel """
		logger.debug( 'MonitorAGiFactory :: send record notification : [%s]' %(message) )
		self._redisPublisher.publish(REDIS_NOTIFICATION_CHANNEL, message)

