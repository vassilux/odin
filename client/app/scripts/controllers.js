//'use strict';

/**
 * Application based controllers
 * Each "core" part of the application has own controller
 *
 */

angular.module('app').controller('AppCtrl', ['$rootScope', '$scope', 'configurationService', 'currentUser', 'i18nNotifications', 
  'localizedMessages', 'socket',
  'networkNotificaitonService', 'asteriskStatusService', 'callsService', 'localize', 'socketEventsDispatcherService', 'authentication', 'configuration',
  function($rootScope, $scope, configurationService, currentUser, i18nNotifications, localizedMessages, socket, 
    networkNotificaitonService, asteriskStatusService, callsService, localize, socketEventsDispatcherService, authentication, configuration) {
    console.log("create AppCtrl");
    var config = configurationService.doStuff();
    if (config != null) {
      console.log("start AppCtrl and get data : " + JSON.stringify(config.host));
    } else {
      console.log("start AppCtrl and get data is null am back");
      return;
    }
    //offer the configuration to others parts
    $rootScope.config = config;
    $scope.notifications = i18nNotifications;
    /*$rootScope.asteriskStatus = asteriskStatus;
    $rootScope.asteriskServersList = [];*/

    localize.setLanguage('fr-FR');
    

    $scope.removeNotification = function(notification) {
      i18nNotifications.remove(notification);
    };

    $rootScope.setWindowTitle = function(title) {
      $rootScope.windowTitle = "Odin : " + title;
    };

    $scope.$on('$routeChangeError', function(event, current, previous, rejection) {
      i18nNotifications.pushForCurrentRoute('errors.route.changeError', 'error', {}, {
        rejection: rejection
      });
    });

    $scope.$on('userLogon', function(event, data) {
      if (currentUser.isAuthenticated()) {
        //Start socket connexion to the server, connection is made explicit cause the config initialized after AppCtrl created. 
        socket.start();
        $scope.connecteSocket(currentUser);
        console.log(" socket started userLogon");
      }
    });

    $scope.$on('userLogout', function(event, data) {
      var data = {
        username: currentUser.userInfo.username,
        isAdmin: currentUser.isAdmin()
      };
      socket.emit('user:left', JSON.stringify(data));
      $scope.setWindowTitle("Odin : Please login");
    });

    
    //
    authentication.requestCurrentUser();

    $scope.connecteSocket = function(data) {
      var data = {
        username: currentUser.userInfo.username,
        isAdmin: currentUser.isAdmin()
      };
      //
      socketEventsDispatcherService.attachAMIEvents(socket);
      //
      socket.emit('user:join', JSON.stringify(data));
      //the server's messages for dispatching are registred by socketEventsDispatcherService
      //I keep direct messages here 
      //If get the follow message try to get the servers status ans actives calls
      socket.on('ami:serverslist', function(data) {
        var message = JSON.parse(data);
        console.log("[AppCtrl] I got ami:serverslist " + data);
        for (var i = 0; i < message.servers.length; i++) {
          console.log("I got the server : " + message.servers[i]);
        };
        if (message.servers.length > 0) {
          asteriskStatusService.setServersList(message.servers);
          var serverName = asteriskStatusService.getActiveServer();
          //
          var data = {
            username: currentUser.userInfo.username,
            servername: serverName //serversList[0]
          };
          socket.emit('ami:getserverstatus', JSON.stringify(data));
          //get actives calls for the active asterisk server
          //please see asteriskStatusService
          callsService.fetchActiveCalls();
        }
      });

      //got the server status message 
      socket.on('ami:serverstatus', function(data) {
        var message = JSON.parse(data);
        console.log("I got ami:serversstatus " + data);
        var peersSip = message.peers.SIP;
        var peersIax = message.peers.IAX2;
        //I clear the two peers array cause the message can be arrived few times and must be fixed on the server side
        var sipPeersFromService = asteriskStatusService.getSipPeers();
        var iaxPeersFromService = asteriskStatusService.getIaxPeers();
        sipPeersFromService.length = 0;
        iaxPeersFromService.length = 0;
        //
        for (var i = 0; i < peersSip.length; i++) {
          var peer = peersSip[i];
          console.log("I got the peer from server : " + peer.peername);
          sipPeersFromService.push(peer);
        };
        //
        for (var i = 0; i < peersIax.length; i++) {
          var peer = peersIax[i];
          console.log("I got the peer from server : " + peer.peername);
          iaxPeersFromService.push(peer);
        };
        //
        //callsService.fetchActiveCalls();
      });

      socket.on('ami:requestresponse', function(data) {
        var message = JSON.parse(data);
        console.log("I got ami:requestresponse " + data);
        var r = message.response;
        var table = "<table class='requestInfo'><tr><td><pre>" + r.join("\n").replace(/\</g, '&lt;').replace(/\>/g, '&gt;') +
          "</pre></td></tr></table>";
        $rootScope.requestResponse = message.response;
        console.log("I produce table " + table);
      });

      socket.on('error', function(data) {
        console.log("socket.on error");
      });

    };

    $scope.disconnecteSocket = function(currentUser) {
      socket.stop();
    };

    $scope.sendMessage = function(event, data) {
      socket.emit(event, data);
    }

    /*socket.on('init', function (data) {
    $scope.name = data.name;
    $scope.users = data.users;
    console.log("socket.on init");
  });

  socket.on('error', function (data) {
    console.log("socket.on error");
  });*/

  }
]);


angular.module('app').controller('HeaderCtrl', ['$scope', '$location', '$route', 'currentUser', 'breadcrumbs', 'notifications', 'localize',
  function($scope, $location, $route, currentUser, breadcrumbs, notifications, localize) {
    console.log("create HeaderCtrl");

    $scope.location = $location;
    $scope.currentUser = currentUser;

    $scope.setEnglishLanguage = function() {
      localize.setLanguage('en-US');
    };

    $scope.setFrenchLanguage = function() {
      localize.setLanguage('fr-FR');
    };

    $scope.home = function() {
      if ($scope.currentUser.isAuthenticated()) {
        console.log("HeaderCtrl $scope.home user Authenticated")
        $location.path('/dashboard');
      } else {
        console.log("HeaderCtrl $scope.home user not Authenticated")
        $location.path('/home');
        $scope.windowTitle = "Odin : home";
      }
    };

    $scope.$on('userLogon', function(event, data) {
      if (currentUser.isAuthenticated()) {
        $location.path('/dashboard');
      }
    });


    $scope.isNavbarActive = function(navBarPath) {
      return navBarPath === breadcrumbs.getFirst().name;

    };

    $scope.hasPendingRequests = function() {
      return false;
    };
  }
]);



angular.module('app').controller('ConfigCtrl', ['$scope', '$location',
  function($scope, $location) {
    /*console.log("create ConfigCtrl");
    var config = configurationService.doStuff();
    if(config != null){
       console.log("start AppCtrl and get data : " + configurationService.doStuff().data);
     }else{
        console.log("start AppCtrl and get data is null ");
     }*/


  }
]);