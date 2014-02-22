/* Peers Services */
angular.module('peers.services', ['ui.bootstrap.dialog'])

.factory('peer', function() {
  var peer = {};
  peer.status = "";
  peer.callerid = "";
  peer.peername = "";
  peer.context = "";
  peer.channeltype = "";
  peer.objecttype = "";
  return peer;
})

.factory('originateCall', function() {
  var originateCall = {};
  originateCall.from = "";
  originateCall.to = "";
  return originateCall;
})

.factory('peerInfoService', ['$rootScope', '$dialog', function($rootScope, $dialog) {

  var peerInfoDialog = null;

  var peerInfoService = {};

  function onPeerInfoDialogClose(success) {
    if(peerInfoDialog) {
      peerInfoDialog.close(success);
      peerInfoDialog = null;
      $rootScope.currentPeer = null;
    }
  }


  peerInfoService.openPeerInfoDialog = function(peer) {
    if(!peerInfoDialog) {
      $rootScope.currentPeer = peer;
      peerInfoDialog = $dialog.dialog();
      peerInfoDialog.open('scripts/peers/peerInfo.tpl.html', 'PeerInfoCtrl').then(onPeerInfoDialogClose);
    }
  };

  peerInfoService.closeInfoDialog = function() {
    onPeerInfoDialogClose(false);
  };

  return peerInfoService;

}])

.factory('peerPropertiesService', ['$rootScope', '$dialog', 'currentUser', 'socket', 
  'asteriskStatusService',
 function($rootScope, $dialog, currentUser, socket, asteriskStatusService) {

  var peerPropertiesDialog = null;

  var peerPropertiesService = {};

  function onPeerPropertiesDialogClose(success) {
    if(peerPropertiesDialog) {
      peerPropertiesDialog.close(success);
      peerPropertiesDialog = null;
      $rootScope.currentPeer = null;
    }
  }

  function fetchPeerProperties(peer) {
    var commandText = "";
    if(peer.channeltype == "SIP") {
      commandText = "sip show peer " + peer.peername;
    } else if(peer.channeltype == "IAX2") {
      commandText = "iax2 show peer " + peer.peername;
    }
    var data = {
      username: currentUser.userInfo.username,
      servername: asteriskStatusService.getActiveServer(),
      textype: 'request',
      command: commandText
    };
    //
    socket.emit('ami:request_info', JSON.stringify(data));
  }

  peerPropertiesService.openPeerPropertiesDialog = function(peer) {
    if(!peerPropertiesDialog) {
      $rootScope.currentPeerProperties = peer;
      peerPropertiesDialog = $dialog.dialog();
      peerPropertiesDialog.open('scripts/peers/peerProperties.tpl.html', 'PeerPropertiesCtrl').then(onPeerPropertiesDialogClose);
    }
    fetchPeerProperties(peer);
  };

  peerPropertiesService.closePropertiesDialog = function() {
    onPeerPropertiesDialogClose(false);
  };

  return peerPropertiesService;

}])

.factory('peerOriginateService', ['$rootScope', '$dialog', 'currentUser', 'socket', 'asteriskStatusService',
  function($rootScope, $dialog, currentUser, socket, asteriskStatusService) {

  var peerOriginateDialog = null;

  var peerOriginateService = {};

  function onPeerOriginateDialogClose(success) {
    if(peerOriginateDialog) {
      peerOriginateDialog.close(success);
      peerOriginateDialog = null;
      $rootScope.currentPeer = null;
    }
  }


  peerOriginateService.openPeerOriginateDialog = function(peer) {
    if(!peerOriginateDialog) {
      $rootScope.currentPeer = peer;
      peerOriginateDialog = $dialog.dialog();
      peerOriginateDialog.open('scripts/peers/peerOriginate.tpl.html', 'PeerOriginateCtrl').then(onPeerOriginateDialogClose);
    }
  };

  peerOriginateService.closeOriginateDialog = function() {
    onPeerOriginateDialogClose(false);
  };

  /**
   * Originate a call
   * @param originateCall, the call object, the object based on $rootScoppe.originateCall
   * @bref Source build by add the channel type of the peer and the peer name
   */
  peerOriginateService.originateCall = function(originateCall) {
    console.log('I originate call : ' + JSON.stringify(originateCall));
    //
    var data = {
      username: currentUser.userInfo.username,
      servername: asteriskStatusService.getActiveServer(),
      type: 'dial',
      source: originateCall.channeltype + "/" + originateCall.source,
      destination: originateCall.destination
    };
    //
    socket.emit('ami:originate', JSON.stringify(data));
    onPeerOriginateDialogClose(false);
  };
  return peerOriginateService;

}])

.factory('peerSpyService', ['$rootScope', '$dialog', 'currentUser', 'socket', 
  'asteriskStatusService', function($rootScope, $dialog, currentUser, socket, asteriskStatusService) {
  var peerSpyDialog = null;
  var peerSpyService = {};

  function onPeerSpyDialogClose(success) {
    if(peerSpyDialog) {
      peerSpyDialog.close(success);
      peerSpyDialog = null;
      $rootScope.spyer = null;
    }
  }

  peerSpyService.spyPeer = function(spyerChannel){
    //
    var data = {
      username: currentUser.userInfo.username,
      servername: asteriskStatusService.getActiveServer(),
      type: 'peer',
      spyer: spyerChannel,
      spyee: $rootScope.spyee.channel
    };
    //
    socket.emit('ami:chan_spy', JSON.stringify(data));
    onPeerSpyDialogClose(false);
  }

  peerSpyService.openSpyDialog = function(spee) {
    if(!peerSpyDialog) {
      $rootScope.spyee = spee;
      peerSpyDialog = $dialog.dialog();
      peerSpyDialog.open('scripts/peers/peerSpy.tpl.html', 'PeerSpyCtrl').then(onPeerSpyDialogClose);
    }
  };

  peerSpyService.closeSpyDialog = function() {
    onPeerSpyDialogClose(false);
  };

  return peerSpyService;

}]);