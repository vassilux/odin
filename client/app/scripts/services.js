'use strict';

/* Services */


// Demonstrate how to register services
// In this case it is a simple value service.
var services = angular.module('app.services', []);

services.value('version', '0.0.1');

var ScopedSocket = function(socket, $rootScope) {
  this.socket = socket;
  this.$rootScope = $rootScope;
  this.listeners = [];
};

ScopedSocket.prototype.removeAllListeners = function() {
  // Remove each of the stored listeners
  for(var i = 0; i < this.listeners.length; i++) {
    var details = this.listeners[i];
    this.socket.removeListener(details.event, details.fn);
  };
};

ScopedSocket.prototype.on = function(event, callback) {
  var socket = this.socket;
  var $rootScope = this.$rootScope;

  // Store the event name and callback so we can remove it later
  this.listeners.push({event: event, fn: callback});

  socket.on(event, function() {
    var args = arguments;
    $rootScope.$apply(function() {
      callback.apply(socket, args);
    });
  });
};

ScopedSocket.prototype.emit = function(event, data, callback) {
  var socket = this.socket;
  var $rootScope = this.$rootScope;

  socket.emit(event, data, function() {
    var args = arguments;
    $rootScope.$apply(function() {
      if (callback) {
        callback.apply(socket, args);
      }
    });
  });
};

/**
 * socket.io helper
 */ 
services.factory('socket', ['$rootScope', 'configurationService', function ($rootScope, configurationService) {
  //the future connection to the server
  var socket = null;
  return {
    start: function(){
      var url = "http://" + $rootScope.config.host + ":" + $rootScope.config.port;
      console.debug("Socket.io connection to the address : " + url)
      socket = io.connect(url,{'force new connection':true});
    },

    stop: function(){
      socket.disconnect();
    },

    on: function (eventName, callback) {
      socket.on(eventName, function () {  
        var args = arguments;
        $rootScope.$apply(function () {
          callback.apply(socket, args);
        });
      });
    },
    emit: function (eventName, data, callback) {
      socket.emit(eventName, data, function () {
        var args = arguments;
        $rootScope.$apply(function () {
          if (callback) {
            callback.apply(socket, args);
          }
        });
      })
    }
  };
}]);



services.factory('networkNotificaitonService', ['$rootScope', function($rootScope) {
    var networkNotificaitonService = {};
    
    networkNotificaitonService.message = '';

    networkNotificaitonService.prepForBroadcast = function(msg) {
        this.message = msg;
        this.broadcastItem();
    };

    networkNotificaitonService.broadcastItem = function() {
        $rootScope.$broadcast('handleBroadcast');
    };

    return networkNotificaitonService;
}]);

/**
 * Configuration service fetch config file from server.
 * The configuration contains information about the server host and port.
 */
services.factory('configurationService', ['$http', function($http) {
    var myData = null;
    var promise = $http.get('config.json').success(function(data){
        console.debug("configurationService got data " + JSON.stringify(data));
        myData = data;
    });

    return {
      promise:promise,

      setData : function(data){
        myData = data;
      },

      doStuff: function() {
        return myData;
      }
    };
}]);

services.factory('asteriskStatusService', ['$rootScope', 'networkNotificaitonService' , function($rootScope, networkNotificaitonService) {
    var asteriskStatus = {};
    var sipPeers = [];
    var iaxPeers = [];
    var asteriskServersList = [];
    //
    asteriskStatus.getSipPeers = function(){
      return sipPeers;
    }

    asteriskStatus.getIaxPeers = function(){
      return iaxPeers;
    }

    asteriskStatus.getServersList = function(){
      return asteriskServersList;
    }

    asteriskStatus.addServer=function(server){
      asteriskServersList.push(server);
    }

    // Helper functions
    asteriskStatus.updatePeerStatus = function(peers, message){
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
       
      });   // foreach 
    }

    //return the active asterisk server used by application
    //Currently only a single server is used
    asteriskStatus.getActiveServer = function(){
      var serverName = "unknown";
      if(asteriskServersList.length > 0){
        serverName = asteriskServersList[0];
      }
      return serverName;
    }

    asteriskStatus.setServersList=function(serversList){
      asteriskServersList = angular.copy(serversList);
    }

    $rootScope.$on('handleBroadcast', function() {
      //shortcut for the global message
      var message = networkNotificaitonService.message;
      console.log("[asteriskStatusService] handleBroadcast " + message.id);
      if(message.id == 'updatepeer'){
        console.log("[PeersCtrl] I got updatepeer for channeltype " + message.peer.channeltype) ;
        if(message.peer.channeltype == "SIP"){
          asteriskStatus.updatePeerStatus(sipPeers, message);
        }else if(message.channeltype == "IAX2"){
          asteriskStatus.updatePeerStatus(iaxPeers, message);
        }
       
      }
        
    }); 

    console.log("factory create asteriskStatus");
    return asteriskStatus;
}]);

//register events handler for the servers messages on the socket service
services.factory('socketEventsDispatcherService', ['$rootScope', 'networkNotificaitonService', function($rootScope, networkNotificaitonService) {
  var socketEventsDispatcherService = {};
  //
  var amiEvents = ["info:asterisk", "info:system", "ami:activecalls", "ami:updatepeer", 
    "ami:createchannel", "ami:updatechannel", "ami:removechannel",
    "ami:createbridge", "ami:updatebridge", "ami:removebridge", 
    "ami:createparkedcall", "ami:removeparkedcall",
    "ami:alarm", "ami:alarmclear", "ami:userevent"
  ];

  $rootScope.dispatchSocketMessage = function(data){
    var object = JSON.parse(data); 
    console.log("I got message from server  " + object.id + " and notify others controllers:  " + data);
    networkNotificaitonService.prepForBroadcast(object);
  };

  socketEventsDispatcherService.attachAMIEvents = function(socket){
    for (var i = 0; i <  amiEvents.length; i++) {
      socket.on( amiEvents[i], function( data ) {
        $rootScope.dispatchSocketMessage(data);      
      } );
    };
  }  

  return socketEventsDispatcherService;
}]);


