/**
 * Active calls and channels services
 * Calls and channels info services separated but the job is very identical
 */
angular.module('calls.services',[])

.factory('callsService', ['$rootScope', 'asteriskStatusService', 'currentUser', 'socket', 'networkNotificaitonService',
  function($rootScope, asteriskStatusService, currentUser, socket, networkNotificaitonService) {
  var callsService = {};
  var calls = [];
  var channels = [];
  var parkedCalls = [];

  callsService.getCalls = function() {
    return calls;
  }

  callsService.getChannels = function() {
    return channels;
  }

  callsService.getParkedCalls = function() {
    return parkedCalls;
  }

  callsService.hangupChannel = function(channel) {
    //
    var data = {
      username: currentUser.userInfo.username,
      servername: asteriskStatusService.getActiveServer(),
      channel: channel
    };
    //
    socket.emit('ami:hangupchannel', JSON.stringify(data));
  };

  callsService.parkChannel = function(channel, announce) {
    var data = {
      username: currentUser.userInfo.username,
      servername: asteriskStatusService.getActiveServer(),
      channel: channel,
      announce: announce
    };
    //
    socket.emit('ami:parkchannel', JSON.stringify(data));
  }

  callsService.transferChannel = function(channel) {
    var realChannel = channel; //.slice(7,channel.lenght)
    var data = {
      username: currentUser.userInfo.username,
      servername: asteriskStatusService.getActiveServer(),
      from: realChannel,
      to: '6005',
      type: 'internalCall'
    };
    //
    console.log('Send the ami:transfer message ' +  JSON.stringify(data));
    socket.emit('ami:transfer', JSON.stringify(data));
  }

  callsService.startMonitor= function(channel, file) {
     var data = {
      username: currentUser.userInfo.username,
      servername: asteriskStatusService.getActiveServer(),
      channel: channel,
      file: file,
      format: 'wav'
    };
    //
    console.log('Send the ami:start_monitor message ' +  JSON.stringify(data));
    socket.emit('ami:start_monitor', JSON.stringify(data));
  }

  callsService.stopMonitor= function(channel) {
     var data = {
      username: currentUser.userInfo.username,
      servername: asteriskStatusService.getActiveServer(),
      channel: channel
    };
    //
    console.log('Send the ami:parkchannel message ' +  JSON.stringify(data));
    socket.emit('ami:stop_monitor', JSON.stringify(data));
  }

  callsService.fetchActiveCalls = function() {

    var servers = asteriskStatusService.getServersList();
    var servername = servers[0]
    var data = {
      username: currentUser.userInfo.username,
      servername: servername
    };
    socket.emit('ami:getactivecalls', JSON.stringify(data));
    console.log('[callsService] emit getactivecalls message to the server for asterisk server ' +  servername);
  };

  //
  $rootScope.$on('handleBroadcast', function() {
      //shortcut for the global message
      var message = networkNotificaitonService.message;
      console.log("[callsService] handleBroadcast " + message.id);
      if(message.id == 'activecalls'){
        callsService.populateChannels(message);
        callsService.populateCalls(message);
      }else if(message.id == 'createchannel'){
        channels.push(angular.copy(message.channel));   
      }else if(message.id == 'updatechannel'){
        callsService.updateChannels(message);
      }else if(message.id == 'removechannel'){
        callsService.removeChannels(message);
      }else if(message.id == 'createbridge'){
        callsService.addCall(message);
      }else if(message.id == 'updatebridge'){
        callsService.updateCalls(message);
      }else if(message.id == 'removebridge'){
        callsService.removeCalls(message);
      }else if(message.id == "createparkedcall"){
        callsService.addParkedCall(message);
      }else if(message.id == "removeparkedcall"){
        callsService.removeParkedCall(message);
      }
        
    }); 
  //start of worker functions
  callsService.populateChannels = function(message){
      console.log("populateChannels");
      for(i=0; i < message.channels.length;i++){
          var channel = message.channels[i];
          channels.push(angular.copy(channel));
      }
    };

    callsService.populateCalls = function(message){
      console.log("populateCalls");
      for(i=0; i < message.bridges.length;i++){
          var call = angular.copy(message.bridges[i]);
          call.calleridnum = "";
          call.calleridname = "";
          call.bridgedidnum = "";
          call.bridgedidname = "";
          var channel = callsService.lookForChannel(call.channel);
            //look for callerid
            if(channel != null){
              call.calleridnum = channel.calleridnum;
              call.calleridname = channel.calleridname;
            }
            //
            var bridgedchannel = callsService.lookForChannel(call.bridgedchannel);
            if(bridgedchannel != null){
              call.bridgedidnum = bridgedchannel.calleridnum;
              call.bridgedidname = bridgedchannel.calleridname;
            }
          calls.push(call);
      }
    };

    callsService.updateChannels = function(message){
      console.log("updateChannels called")
      for(i=0; i < channels.length;i++){
          var channel = channels[i];
          if(channel.uniqueid == message.channel.uniqueid){
            channel.state = message.channel.state; 
            channel.calleridnum = message.channel.calleridnum;
            channel.calleridname = message.channel.calleridname;
            channel.starttime = message.channel.starttime;
            channel.monitor = message.channel.monitor;
            break;
          }
        }
    };

    callsService.removeChannels = function(message){
      for(i=0; i < channels.length;i++){
          var channel = channels[i];
          if(channel.uniqueid == message.channel.uniqueid){
            channels.splice(i,1);
            break;
          }
      }
    }

    /**
     *Look for channel by channel id
     *Uniqueid doesn't use  
     */
    callsService.lookForChannel=function(channelId){
      for(i=0; i < channels.length;i++){
          var channel = channels[i];
          if(channel.channel == channelId){
            return channel;
          }
      }
      return null;
    }

    /**
     *Add a call to the scope calls
     *Callerid initialized to the empty string and updated by the message updatebridge
     */
   callsService.addCall=function(message){
      var call = angular.copy(message.bridge);
      call.calleridnum = "";
      call.calleridname = "";
      call.bridgedidnum = "";
      call.bridgedidname = "";
      calls.push(call); 
    }

    /**
     *Update state of a call 
     *Initialize the caller and callee informations
     */
    callsService.updateCalls = function(message){
      for(i=0; i < calls.length;i++){
          var call = calls[i];
          if(call.bridgeduniqueid == message.bridge.bridgeduniqueid){
            call.status = message.bridge.status; 
            call.linktime = message.bridge.linktime; 
            var channel = callsService.lookForChannel(call.channel);
            //look for callerid
            if(channel != null){
              call.calleridnum = channel.calleridnum;
              call.calleridname = channel.calleridname;
            }
            //
            var bridgedchannel = callsService.lookForChannel(message.bridge.bridgedchannel);
            if(bridgedchannel != null){
              call.bridgedidnum = bridgedchannel.calleridnum;
              call.bridgedidname = bridgedchannel.calleridname;
            }
            break;
          }
      }
       
    }

    /**
     *Remove a call from the scope
     */
    callsService.removeCalls = function(message){
      for(i=0; i < calls.length;i++){
          var call = calls[i];
          if(call.bridgeduniqueid == message.bridge.bridgeduniqueid){
            calls.splice(i,1);
            break;
          }
        }
    }

    callsService.addParkedCall = function(message){
      console.log("callsService.addParkedCall  ");
      var parkedCall = angular.copy(message.parkedcall);
      parkedCalls.push(parkedCall); 
    }

    callsService.removeParkedCall = function(message){
      var parkedChannel = message.parkedcall.channel;
      for(i=0; i < parkedCalls.length;i++){
        var parkedCall = parkedCalls[i];
        if(parkedCall.channel == parkedChannel){
          parkedCalls.splice(i,1);
          break;
        }
      }

    }
  //end of worker functions
  //prefetch active calls

  return callsService;

}])

.factory('transferCall', function() {
  var transferCall = {};
  transferCall.source = "";
  transferCall.destination = "";
  return transferCall;
})

.factory('callInfoService', ['$rootScope', '$dialog', function($rootScope, $dialog) {
  //the reference to the call's info dialog
  var callInfoDialog = null;
  // the service itself
  var calllInfoService = {};

  function onCallInfoDialogClose(success) {
    if(callInfoDialog) {
      callInfoDialog.close(success);
      callInfoDialog = null;
      $rootScope.currentCall = null;
    }
  }

  calllInfoService.showCallInfo = function(call) {
    if(!callInfoDialog) {
      $rootScope.currentCall = angular.copy(call);
      callInfoDialog = $dialog.dialog();
      callInfoDialog.open('scripts/calls/callInfo.tpl.html', 'CallInfoCtrl').then(onCallInfoDialogClose);
    }
  };

  calllInfoService.closeInfoDialog = function() {
    onCallInfoDialogClose(false);
  };

  return calllInfoService;

}])

.factory('channelInfoService', ['$rootScope', '$dialog', function($rootScope, $dialog) {
   //the reference to the channel's info dialog
  var channelInfoDialog = null;
  // the service itself
  var channelInfoService = {};

  function onChannelInfoDialogClose(success) {
    if(channelInfoDialog) {
      channelInfoDialog.close(success);
      channelInfoDialog = null;
      $rootScope.currentChannel = null;
    }
  }


  channelInfoService.showChannelInfo = function(channel) {
    if(!channelInfoDialog) {
      $rootScope.currentChannel = angular.copy(channel);
      channelInfoDialog = $dialog.dialog();
      channelInfoDialog.open('scripts/calls/channelInfo.tpl.html', 'ChannelInfoCtrl').then(onChannelInfoDialogClose);
    }
  };

  channelInfoService.closeInfoDialog = function() {
    onChannelInfoDialogClose(false);
  };

  return channelInfoService;

}])


.factory('channelSpyService', ['$rootScope', '$dialog', 'currentUser', 'socket', 
  'asteriskStatusService', function($rootScope, $dialog, currentUser, socket, asteriskStatusService) {

  var channelSpyDialog = null;

  var channelSpyService = {};

  function onChannelSpyDialogClose(success) {
    if(channelSpyDialog) {
      channelSpyDialog.close(success);
      channelSpyDialog = null;
    }
  }

  channelSpyService.spyChannel = function(spyer){
    console.log('Prepare spy  for channel spyer: ' +  spyer + ' spyee channel ' + $rootScope.spyee.channel);
    //
    var data = {
      username: currentUser.userInfo.username,
      servername: asteriskStatusService.getActiveServer(),
      type: 'number',
      spyer: spyer,
      spyee: $rootScope.spyee.channel
    };
    //
    socket.emit('ami:chan_spy', JSON.stringify(data));
    onChannelSpyDialogClose(false);
  }

  channelSpyService.openSpyDialog = function(spee) {
    if(!channelSpyDialog) {
      $rootScope.spyee = spee;
      channelSpyDialog = $dialog.dialog();
      channelSpyDialog.open('scripts/calls/channelSpy.tpl.html', 'ChannelSpyCtrl').then(onChannelSpyDialogClose);
    }
  };

  channelSpyService.closeSpyDialog = function() {
    onChannelSpyDialogClose(false);
  };

  return channelSpyService;

}])

.factory('callTransferService', ['$rootScope', '$dialog', 'currentUser', 'asteriskStatusService', 'socket',
   function($rootScope, $dialog, currentUser, asteriskStatusService, socket) {
   //the reference to the transfer dialog
  var callTransferDialog = null;
  // the service itself
  var callTransferService = {};

  function onTransferCallDialogClose(success) {
    if(callTransferDialog) {
      callTransferDialog.close(success);
      callTransferDialog = null;
      $rootScope.currentTransferCall = null;
    }
  }


  callTransferService.showTransferDialog = function(call) {
    if(!callTransferDialog) {
      $rootScope.currentTransferCall = angular.copy(call);
      callTransferDialog = $dialog.dialog();
      callTransferDialog.open('scripts/calls/transferCall.tpl.html', 'TransferCtrl').then(onTransferCallDialogClose);
    }
  };

  callTransferService.closeTransferDialog = function() {
    onTransferCallDialogClose(false);
  };

  callTransferService.transferCall = function(){
    //
    var data = {
      username: currentUser.userInfo.username,
      servername: asteriskStatusService.getActiveServer(),
      type: 'transfer',
      source: $rootScope.currentTransferCall.source,
      destination: $rootScope.currentTransferCall.destination
    };
    //
    socket.emit('ami:transfer', JSON.stringify(data));
    onTransferCallDialogClose(false);
  };


  return callTransferService;

}]);