angular.module('peers', [])

.config(['$routeProvider', function ($routeProvider) {
  $routeProvider.when('/peers', {
    templateUrl:'scripts/peers/peers.tpl.html',
    controller:'PeersCtrl'
   });
}])

.controller('PeerInfoCtrl', ['$rootScope', '$scope','peerInfoService',
  function ($rootScope, $scope, peerInfoService) {

  $scope.closePeerInfo = function(){
    peerInfoService.closeInfoDialog();
  };

}])

.controller('PeerSpyCtrl', ['$rootScope', '$scope','peerSpyService',
  function ($rootScope, $scope, peerSpyService) {

  $scope.closeSpy = function(){
    peerSpyService.closeSpyDialog();
  };

  $scope.spyPeer = function(spyer){
    var spyerChannel = "SIP/" + spyer;
    peerSpyService.spyPeer(spyerChannel);
  };

}])

.controller('PeerPropertiesCtrl', ['$rootScope', '$scope','peerPropertiesService',
  function ($rootScope, $scope, peerPropertiesService) {

  $scope.closePeerProperties = function(){
    peerPropertiesService.closePropertiesDialog();
  };

}])

.controller('PeerOriginateCtrl', ['$rootScope', '$scope','peerOriginateService',
  function ($rootScope, $scope, peerOriginateService) {

  $scope.peerOriginate = function (){
    var source = $rootScope.originateCall.source;
    var destination = $rootScope.originateCall.destination;
    peerOriginateService.originateCall($rootScope.originateCall);
  };

  $scope.closePeerOriginate = function(){
    peerOriginateService.closeOriginateDialog();
  };

}])

.controller('PeersCtrl', ['$rootScope', '$scope', '$location', 
  'peer', 'networkNotificaitonService', 'socket','currentUser', 'asteriskStatusService', 'peerInfoService', 
  'peerOriginateService', 'peerPropertiesService', 'originateCall', 'peerSpyService',
  function ($rootScope, $scope, $location, peer, networkNotificaitonService, socket,currentUser,asteriskStatusService, peerInfoService, 
            peerOriginateService, peerPropertiesService, originateCall, peerSpyService) {
    console.log("I create scope value for peers,  PeersCtrl called");

    var data = {username: currentUser.userInfo.username, isAdmin: currentUser.isAdmin()};
    $scope.peersSip = [];
    $scope.peersIax = [];
    var sipPeersFromService = asteriskStatusService.getSipPeers();
    var iaxPeersFromService = asteriskStatusService.getIaxPeers();
    $scope.peersSip = sipPeersFromService;
    $scope.peersIax = iaxPeersFromService

   /* angular.forEach($rootScope.asteriskStatus.peersSip, function(peer, keyPeer) {
        $scope.peersSip.push(angular.copy(peer));
    });    
    

    var peersIax = [];
    angular.forEach($rootScope.asteriskStatus.peersIax, function(peer, keyPeer) {
        $scope.peersIax.push(angular.copy(peer));
        console.log("I got the iax peer from server : " + peer.peername);       
    });   */ 

 

    $scope.originate = function(peer){
      console.log("originate called from : " + peer.peername);
      $rootScope.originateCall = {};
      $rootScope.originateCall.channeltype = peer.channeltype;
      $rootScope.originateCall.source = peer.peername;
      $rootScope.originateCall.destination = "";
      peerOriginateService.openPeerOriginateDialog();
    };

    $scope.canBeSpyed=function(peer){
      if(peer.calls > 0){
        return true;
      }
      return false;
    }

    $scope.showPeerInfo = function(peer){
      console.log("showPeerInfo called for peer : " + peer.peername);
      peerInfoService.openPeerInfoDialog(peer);
    };

    $scope.spyPeer = function(peer){
      console.log("spyPeer called for peer : " + peer.peername);
      peerSpyService.openSpyDialog(peer);
    };

    $scope.showProperties = function(peer){
      console.log("properties called for : " + peer.peername);
      peerPropertiesService.openPeerPropertiesDialog(peer);
    };

    // Helper functions
    updatePeerStatus = function(peers, message){
      angular.forEach(peers, function(peer, keyPeer) {
        if(peer.peername == message.peer.peername){
          peer.status = message.peer.status;
          peer.calls = message.peer.calls;
          peer.callstatus = 0;
          if(peer.calls  > 0){
            //I change calls status to indicate that there are the actives calls
            peer.callstatus = 1;
          }
          peer.callerid = message.peer.callerid;
          console.log("[PeersCtrl] I updated peer : " + peer.peername);
        }
       
      }); 
    }

}]);

