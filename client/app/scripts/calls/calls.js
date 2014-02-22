/**
 *Calls and channels module
 *
 */
angular.module('calls', [])

.config(['$routeProvider',
  function($routeProvider) {
    $routeProvider.when('/calls', {
      templateUrl: 'scripts/calls/calls.tpl.html',
      controller: 'CallsCtrl'
    });
  }
])

.controller('CallInfoCtrl', ['$rootScope', '$scope', 'callInfoService',
  function($rootScope, $scope, callInfoService) {

    $scope.closeCallInfo = function() {
      callInfoService.closeInfoDialog();
    };

  }
])

.controller('ChannelInfoCtrl', ['$rootScope', '$scope', 'channelInfoService',
  function($rootScope, $scope, channelInfoService) {

    $scope.closeChannelInfo = function() {
      channelInfoService.closeInfoDialog();
    };

  }
])

.controller('TransferCtrl', ['$rootScope', '$scope', 'callTransferService',
  function($rootScope, $scope, callTransferService) {

    /**
     *
     */
    $scope.transferCall = function() {
      console.log("$scope.transferCall called")
      callTransferService.transferCall();
    }

    /**
     *
     */
    $scope.cancelTransfer = function() {
      console.log("$scope.cancelTransfer called")
      callTransferService.closeTransferDialog();
    }

  }
])

.controller('ChannelSpyCtrl', ['$rootScope', '$scope','channelSpyService',
  function ($rootScope, $scope, channelSpyService) {

  $scope.spyChannel = function(spyer){
    channelSpyService.spyChannel(spyer);    
  };

  $scope.closeSpyChannel = function(){
    channelSpyService.closeSpyDialog();
  };

}])


.controller('CallsCtrl', ['$rootScope', '$scope', 'networkNotificaitonService', 'asteriskStatusService',
  'callsService', 'channelInfoService', 'callInfoService', 'callTransferService', 'transferCall','channelSpyService',
  function($rootScope, $scope, networkNotificaitonService, asteriskStatusService, callsService,
    channelInfoService, callInfoService, callTransferService, transferCall,channelSpyService) {
    console.log("Create CallsCtrl");
    $scope.channels = [];
    $scope.calls = [];
    $scope.parkedCalls = [];
    //
    var channels = callsService.getChannels();
    var calls = callsService.getCalls();
    var parkedCalls = callsService.getParkedCalls();
    //
    $scope.channels = channels;
    $scope.calls = calls;
    $scope.parkedCalls = parkedCalls;

    /**
     *
     */
    $scope.hangupChannel = function(channel) {
      callsService.hangupChannel(channel);
    };

    /**
     *
     */
    $scope.parkChannel = function(channel, announce) {
      callsService.parkChannel(channel, announce);
    }

    /**
     *
     */
    $scope.transferChannel = function(channel) {
      transferCall = {};
      transferCall.source = channel;
      transferCall.destination = "";
      callTransferService.showTransferDialog(transferCall);
    }

    /**
     *
     */
    $scope.showChannelInfo = function(channel) {
      channelInfoService.showChannelInfo(channel);
    };

    $scope.isMonitoredChannel = function(channel) {
      if (channel.monitor == true) {
        return true;
      }
      return false;
    };



    /**
     *
     */
    $scope.startMonitor = function(channel) {
      callsService.startMonitor(channel.channel, channel.uniqueid);
    }

    /**
     *
     */
    $scope.stopMonitor = function(channel) {
      callsService.stopMonitor(channel.channel);
    }

    /**
     *
     */
    $scope.spyChannel = function(channel) {
      channelSpyService.openSpyDialog(channel);
    }

    /**
     *
     */
    $scope.showCallInfo = function(call) {
      callInfoService.showCallInfo(call);

    };
    /**
     *Look for channel by channel id
     *Uniqueid doesn't use
     */
    $scope.lookForChannel = function(channelId) {
      for (i = 0; i < $scope.channels.length; i++) {
        var channel = $scope.channels[i];
        if (channel.channel == channelId) {
          return channel;
        }
      }
      return null;
    }

    /**
     *Add a call to the scope calls
     *Callerid initialized to the empty string and updated by the message updatebridge
     */
    $scope.addCall = function(message) {
      var call = angular.copy(message.bridge);
      call.calleridnum = "";
      call.calleridname = "";
      call.bridgedidnum = "";
      call.bridgedidname = "";
      $scope.calls.push(call);
    }
  }
]);