angular.module('dashboard', [])

.config(['$routeProvider',
  function($routeProvider) {
    $routeProvider.when('/dashboard', {
      templateUrl: 'scripts/dashboard/dashboard.tpl.html',
      controller: 'DashboardCtrl'

    });
  }
])

.factory('asteriskinfo', function() {
  var asteriskinfo = {};
  asteriskinfo.version = "";
  asteriskinfo.upTime = "";
  asteriskinfo.reloadTime = "";
  asteriskinfo.channelsInUse = "";
  return asteriskinfo;
})

.factory('osinfostats', function() {
  var osinfostats = {};
  osinfostats.upTime = "";
  osinfostats.cpuLoad = "";
  osinfostats.totalRamInMachine = "";
  osinfostats.totalRamUsed = "";
  osinfostats.totalRamFree = "";
  osinfostats.totalRamShared = "";
  osinfostats.totalSwap = "";
  osinfostats.totalDiskSize = "";
  osinfostats.totalDiskAvailableSize = "";
  osinfostats.totalDiskUsedSpace = "";
  osinfostats.totalDiskPercSpaceUsed = "";
  return osinfostats;
})

.factory('clusterinfo', function() {
  var clusterinfo = {};
  clusterinfo.nodes = new Array();
  clusterinfo.nodes.push({
    name: 'astnode1',
    status: 'online'
  });
  clusterinfo.nodes.push({
    name: 'astnode2',
    status: 'standby'
  });

  return clusterinfo;
})

.controller('DashboardCtrl', ['$rootScope', '$scope', '$location', '$filter', '$timeout',
  'asteriskinfo', 'osinfostats', 'clusterinfo', 'networkNotificaitonService', 'dashboardSysInfoService',
  function($rootScope, $scope, $location, $filter, $timeout, asteriskinfo, osinfostats, clusterinfo, networkNotificaitonService, dashboardSysInfoService) {
    console.log("I create scope value for asteriskInfo ");
    $scope.setWindowTitle("Dashboard");
    $scope.asteriskInfo = asteriskinfo;
    $scope.osinfostats = osinfostats;
    $scope.clusterinfo = clusterinfo;

    dashboardSysInfoService.getSysInfo(function(status, data) {
      //var packet = JSON.parse(data);
      //"asterisk": {"processedcalls": "2", "uptime": " 4 hours, 24 minutes, 33 seconds ", "activecalls": "0", "reloadtime": " 3 hours, 38 minutes, 44 seconds "}
      processSysInfoCallback(status, data);
      //$scope.asteriskInfo = angular.copy(data.message.asterisk)
    });

    var fetch;
    $scope.fetchSysInfo = function() {
       fetch = $timeout(function() {
      dashboardSysInfoService.getSysInfo(function(status, data) {
        //"asterisk": {"processedcalls": "2", "uptime": " 4 hours, 24 minutes, 33 seconds ", "activecalls": "0", "reloadtime": " 3 hours, 38 minutes, 44 seconds "}
        processSysInfoCallback(status, data);
        $scope.fetchSysInfo();
      });

    }, 15000);
    };

   

    $scope.fetchSysInfo();

    function processSysInfoCallback(status, data) {
      if(data == undefined || data.message == undefined || data.message.asterisk == undefined){
        return;
      }
      $scope.asteriskInfo = angular.copy(data.message.asterisk);
      $scope.osinfostats = angular.copy(data.message);
    }

    function timeticksToString(tt) {
      var secs = Math.floor(tt / 100);
      var days = Math.floor(secs / 60 / 60 / 24);
      secs -= days * 60 * 60 * 24;
      var hrs = Math.floor(secs / 60 / 60);
      secs -= hrs * 60 * 60;
      var mins = Math.floor(secs / 60);
      secs -= mins * 60;
      return days + " days " + hrs + " hours " + mins + " minutes " + secs + " seconds";

    }

    function bytesToSize(bytes) {
      var sizes = ['n/a', 'Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
      var i = +Math.floor(Math.log(bytes) / Math.log(1024));
      return (bytes / Math.pow(1024, i)).toFixed(i ? 1 : 0) + ' ' + sizes[isNaN(bytes) ? 0 : i + 1];
    }

    function bytesToSize2(bytes) {
      var sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
      if (bytes == 0 || !isNumber(bytes)) return 'n/a';
      var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
      return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
    }

    function isNumber(o) {
      return !isNaN(o - 0) && o !== null && o !== "" && o !== false;
    }


    function secondsToString(seconds) {
      var numdays = Math.floor(seconds / 86400);
      var numhours = Math.floor((seconds % 86400) / 3600);
      var numminutes = Math.floor(((seconds % 86400) % 3600) / 60);
      var numseconds = Math.floor(((seconds % 86400) % 3600) % 60);

      return numdays + " days " + numhours + " hours " + numminutes + " minutes " + numseconds + " seconds";
    }

    $scope.$on('handleBroadcast', function() {
      console.log("handleBroadcast " + networkNotificaitonService.message.id);
      if (networkNotificaitonService.message.id == 'info:asterisk') {
        $scope.asteriskInfo.version = networkNotificaitonService.message.version;
        $scope.asteriskInfo.upTime = timeticksToString(networkNotificaitonService.message.upTime);
        //$filter('date')(new Date(networkNotificaitonService.message.upTime * 1000),'dd/MM/y hh:mm:ss');
        $scope.asteriskInfo.reloadTime = timeticksToString(networkNotificaitonService.message.reloadTime);
        $scope.asteriskInfo.channelsInUse = networkNotificaitonService.message.channelsInUse;
        //
        $scope.asteriskInfo.callsActive = networkNotificaitonService.message.callsActive;
        $scope.asteriskInfo.callsProcessed = networkNotificaitonService.message.callsProcessed;
      } else if (networkNotificaitonService.message.id == 'info:system') {
        $scope.osinfostats.upTime = timeticksToString(networkNotificaitonService.message.upTime);
        $scope.osinfostats.cpuLoad = networkNotificaitonService.message.cpuLoad;
        $scope.osinfostats.totalRamInMachine = bytesToSize(networkNotificaitonService.message.totalRamInMachine);
        $scope.osinfostats.totalRamUsed = bytesToSize(networkNotificaitonService.message.totalRamUsed);
        $scope.osinfostats.totalRamFree = bytesToSize(networkNotificaitonService.message.totalRamFree);
        $scope.osinfostats.totalRamShared = bytesToSize(networkNotificaitonService.message.totalRamShared);
        $scope.osinfostats.totalSwap = bytesToSize(networkNotificaitonService.message.totalSwap);
        //
        $scope.osinfostats.totalDiskSize =
          bytesToSize(networkNotificaitonService.message.totalDiskSize);
        $scope.osinfostats.totalDiskAvailableSize =
          bytesToSize(networkNotificaitonService.message.totalDiskAvailableSize);
        $scope.osinfostats.totalDiskUsedSpace =
          bytesToSize(networkNotificaitonService.message.totalDiskUsedSpace);
        $scope.osinfostats.totalDiskPercSpaceUsed =
          networkNotificaitonService.message.totalDiskPercSpaceUsed;

      }

    });

  }
]);

/**, asteriskinfo, osinfostats**/
/**, 'asteriskinfo', 'osinfostats',**/

/*.factory('clusterinfo', function () {
  var clusterinfo = {};
  clusterinfo.nodes={};

  return clusterinfo;
})*/