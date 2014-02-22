//os analyzer 
//I use the redis server to publish the os status informations.
var net = require('net');
var path = require('path');
var log4js = require("log4js");
var cjson = require('cjson');
var config = cjson.load('./config/config.json');
var snmp = require('snmp-native');
var _ = require('underscore');
var util = require('util');
var async = require('async');
//
var logfile = path.join(__dirname, '/logs/snmp_analyzer.log');

var host = 'localhost';
var community = 'kesix';



log4js.addAppender(require('log4js/lib/appenders/file').appender(logfile), 'snmp_analyzer');
log4js.loadAppender('file');
log4js.addAppender(log4js.appenders.file(logfile), 'os.analyzer');
var logger = log4js.getLogger('os.analyzer');
logger.setLevel(config.OS_ANALYZER_LOG_LEVEL);

var redis = require("redis");
var redisClient = redis.createClient(config.redis_port, config.redis_host);




/*var session2 = new snmp.Session({
	host: host,
	community: community
});
session2.getSubtree({
	oid: oid
}, function(err, varbinds) {
	if(err) {
		console.log("session 2 " + err);
	} else {
		_.each(varbinds, function(vb) {
			console.log('Name of interface ' + _.last(vb.oid) + ' is "' + vb.value + '"');
		});
	}

	session2.close();
});*/

/*var oidAstStr = '.1.3.6.1.4.1.22736.1';
oidAst = _.map(_.compact(oidAstStr.split('.')), function (x) { return parseInt(x, 10); });


var session3= new snmp.Session({ host: host, community: community });
session3.getSubtree({ oid: oidAst }, function (err, varbinds) {
    if (err) {
        console.log(err);
    } else {
        _.each(varbinds, function (vb) {
            console.log('Name of asterisk ' + _.last(vb.oid)  + ' is "' + vb.value + '"');
        });
    }

    session3.close();
});*/

function snmpSystemJob(){
	var sysOids = [];
	//.1.3.6.1.2.1.1.3.0
	var oidSysUpTime = [1 ,3 ,6 ,1 ,2 ,1 ,1 ,3 ,0]; //[1 ,3 ,6 ,1 ,2 ,1 ,25 ,1,1,0]; //
	var oidSysCPULoad5 = [1 , 3, 6 ,1 ,4 , 1, 2021,10 ,1 ,3 ,2];
	var oidSysTotalRamInMachine=[1,3,6,1,4,1,2021,4,5,0];
	var oidSysTotalRamUsed = [1,3,6,1,4,1,2021,4,6,0];
	var oidSysTotalRamFree = [1,3,6,1,4,1,2021,4,11,0];
	var oidSysTotalRamShared = [1,3,6,1,4,1,2021,4,13,0];
	var oidSysTotalSwap= [1,3,6,1,4,1,2021,4,4,0];
	//
	var oidSysDiskTotalSize = [1,3,6,1,4,1,2021,9,1,6,1];
	var oidSysDiskAvailableSize=[1,3,6,1,4,1,2021,9,1,7,1];
	var oidSysDiskUsedSpace = [1,3,6,1,4,1,2021,9,1,8,1];
	var oidSysDiskPercSpaceUsed = [1,3,6,1,4,1,2021,9,1,9,1]; 
	//
	sysOids.push(oidSysUpTime);
	sysOids.push(oidSysCPULoad5);
	//
	sysOids.push(oidSysTotalRamInMachine);
	sysOids.push(oidSysTotalRamUsed);
	sysOids.push(oidSysTotalRamFree);
	sysOids.push(oidSysTotalRamShared);
	sysOids.push(oidSysTotalSwap);
	//
	sysOids.push(oidSysDiskTotalSize);
	sysOids.push(oidSysDiskAvailableSize);
	sysOids.push(oidSysDiskUsedSpace);
	sysOids.push(oidSysDiskPercSpaceUsed);
	//
	var session = new snmp.Session({
		host: host,
		community: community
	});
	//
	session.getAll({
		oids: sysOids
	}, function(err, varbinds) {
		var msg = {id: 'info:system', upTime: '0', cpuLoad: '0',
			totalRamInMachine: '0', totalRamUsed: '0', totalRamFree: '0', totalRamShared: '0',
			totalSwap: '0', totalDiskSize: '0', totalDiskAvailableSize: '0', totalDiskUsedSpace: '0',
			totalDiskPercSpaceUsed: '0'};
		//
		_.each(varbinds, function(vb) {
			if(snmp.compareOids(vb.oid, oidSysUpTime) == 0) {
				//logger.debug("ods system uptime  " + vb.oid + ' = ' + vb.value);
				msg.upTime = vb.value;
			}else if(snmp.compareOids(vb.oid, oidSysCPULoad5) == 0) {
				//logger.debug("ods system cpu load " + vb.oid + ' = ' + vb.value);
				msg.cpuLoad = vb.value;
			}else if(snmp.compareOids(vb.oid, oidSysTotalRamInMachine) == 0) {
				msg.totalRamInMachine = vb.value * 1024;
			}else if(snmp.compareOids(vb.oid, oidSysTotalRamUsed) == 0) {
				msg.totalRamUsed = vb.value;
			}else if(snmp.compareOids(vb.oid, oidSysTotalRamFree) == 0) {
				msg.totalRamFree = vb.value * 1024;
			}else if(snmp.compareOids(vb.oid, oidSysTotalRamShared) == 0) {
				msg.totalRamShared = vb.value * 1024;
			}else if(snmp.compareOids(vb.oid, oidSysTotalSwap) == 0) {
				msg.totalSwap = vb.value * 1024;
			}else if(snmp.compareOids(vb.oid, oidSysDiskTotalSize) == 0) {
				msg.totalDiskSize = vb.value * 1024;
			}else if(snmp.compareOids(vb.oid, oidSysDiskAvailableSize) == 0) {
				msg.totalDiskAvailableSize = vb.value * 1024;
			}else if(snmp.compareOids(vb.oid, oidSysDiskUsedSpace) == 0) {
				msg.totalDiskUsedSpace = vb.value * 1024;
			}else if(snmp.compareOids(vb.oid, oidSysDiskPercSpaceUsed) == 0) {
				msg.totalDiskPercSpaceUsed = vb.value;
			}else {
				logger.debug("ods " + vb.oid + ' = ' + vb.value);
			}

		});
		redisClient.publish( 'odin_snmp_channel', JSON.stringify(msg));
		session.close();
	});
	//

}

function snmpAsteriskJob() {
	//fetching asterisk infos 
	var asteriskOids = [];
	var oidAstVersion = [1, 3, 6, 1, 4, 1, 22736, 1, 1, 1, 0];
	var oidAstUpTime = [1, 3, 6, 1, 4, 1, 22736, 1, 2, 1, 0];
	var oidAstReloadTime = [1, 3, 6, 1, 4, 1, 22736, 1, 2, 2, 0];
	var oidAstChannelsInUse = [1, 3, 6, 1, 4, 1, 22736, 1, 5, 1, 0];
	var oidAstConfigCallsActive = [1, 3, 6, 1, 4, 1, 22736, 1, 2, 5, 0];
	var oidAstConfigCallsProcessed = [1, 3, 6, 1, 4, 1, 22736, 1, 2, 6, 0];
	//
	asteriskOids.push(oidAstVersion);
	asteriskOids.push(oidAstUpTime);
	asteriskOids.push(oidAstReloadTime);
	asteriskOids.push(oidAstChannelsInUse);
	asteriskOids.push(oidAstConfigCallsActive);
	asteriskOids.push(oidAstConfigCallsProcessed);


	var session = new snmp.Session({
		host: host,
		community: community
	});
	//fetch asterisk infos
	session.getAll({
		oids: asteriskOids
	}, function(err, varbinds) {
		var msg = {id: 'info:asterisk', version: '', upTime: '0', reloadTime: '0', channelsInUse: '0',
					callsActive:'0', callsProcessed: '0'};
		//
		_.each(varbinds, function(vb) {
			if(snmp.compareOids(vb.oid, oidAstVersion) == 0) {
				msg.version = vb.value;
			} else if(snmp.compareOids(vb.oid, oidAstUpTime) == 0) {
				msg.upTime = vb.value;
			} else if(snmp.compareOids(vb.oid, oidAstReloadTime) == 0) {
				msg.reloadTime = vb.value;
			} else if(snmp.compareOids(vb.oid, oidAstChannelsInUse) == 0) {
				msg.channelsInUse = vb.value;
			} else if(snmp.compareOids(vb.oid, oidAstConfigCallsActive) == 0){
				msg.callsActive = vb.value;
			}else if(snmp.compareOids(vb.oid, oidAstConfigCallsProcessed) == 0){
				msg.callsProcessed = vb.value;
			} else {
				logger.debug("ods " + vb.oid + ' = ' + vb.value);
			}

		});
		redisClient.publish( 'odin_snmp_channel', JSON.stringify(msg));
		session.close();
	});
}

function snmpPacemaker() {
	//fetching asterisk infos 
	var pacemakerOids = [];
	var oidCrmNode = [1, 3, 6, 1, 4, 1, 32723.1];
	var oidCrmRsc = [1, 3, 6, 1, 4, 1, 32723.2];
	//
	asteriskOids.push(oidAstVersion);
	asteriskOids.push(oidAstUpTime);
	asteriskOids.push(oidAstReloadTime);
	asteriskOids.push(oidAstChannelsInUse);
	asteriskOids.push(oidAstConfigCallsActive);
	asteriskOids.push(oidAstConfigCallsProcessed);


	var session = new snmp.Session({
		host: host,
		community: community
	});
	//fetch asterisk infos
	session.getAll({
		oids: asteriskOids
	}, function(err, varbinds) {
		var msg = {id: 'info:asterisk', version: '', upTime: '0', reloadTime: '0', channelsInUse: '0',
					callsActive:'0', callsProcessed: '0'};
		//
		_.each(varbinds, function(vb) {
			if(snmp.compareOids(vb.oid, oidAstVersion) == 0) {
				msg.version = vb.value;
			} else if(snmp.compareOids(vb.oid, oidAstUpTime) == 0) {
				msg.upTime = vb.value;
			} else if(snmp.compareOids(vb.oid, oidAstReloadTime) == 0) {
				msg.reloadTime = vb.value;
			} else if(snmp.compareOids(vb.oid, oidAstChannelsInUse) == 0) {
				msg.channelsInUse = vb.value;
			} else if(snmp.compareOids(vb.oid, oidAstConfigCallsActive) == 0){
				msg.callsActive = vb.value;
			}else if(snmp.compareOids(vb.oid, oidAstConfigCallsProcessed) == 0){
				msg.callsProcessed = vb.value;
			} else {
				logger.debug("ods " + vb.oid + ' = ' + vb.value);
			}

		});
		redisClient.publish( 'odin_snmp_channel', JSON.stringify(msg));
		session.close();
	});
}



var snmpJobInterval = 2000;

(function shedule() {
	setTimeout(function doIt() {
			async.series([

			function(next) {
				snmpAsteriskJob();
				next();
			}, 

			function(next) {
				snmpSystemJob();
				next();
			},
			function(next) {
				console.log("placeholder");
				next();
			}, ], function(err, results) {
				if(err) {
					logger.error('I got error :  ' + err  + ' and re-try reschedule job.');
				} else {
					logger.debug('I did the jobs with success.');
				}
				shedule();
			});

	}, snmpJobInterval);

}());