// Based loosely around work by Witold Szczerba - https://github.com/witoldsz/angular-http-auth
angular.module('authentication.service', [
  'authentication.currentUser', 'authentication.retryQueue', 'authentication.login', 'ui.bootstrap.dialog'
])

// The authentication is the public API for this module.  Application developers should only need to use this service and not any of the others here.
.factory('authentication',
          ['$rootScope', '$http', '$location', '$q', 'authenticationRetryQueue', 'currentUser', '$dialog',
  function( $rootScope,   $http,   $location,   $q,   queue,                      currentUser,   $dialog) {

  // We need a way to refresh the page to clear any data that has been loaded when the user logs out
  //  a simple way is to redirect to the root of the application but this could be made more sophisticated
  function redirect(url) {
    url = url || '/';
    $location.path(url);
  }

  var loginDialog = null;
  function openLoginDialog() {
    if ( !loginDialog ) {
      loginDialog = $dialog.dialog();
      loginDialog.open('scripts/common/authentication/login/form.tpl.html', 'LoginFormController').then(onLoginDialogClose);
    }
  }
  function closeLoginDialog(success) {
    if (loginDialog) {
      loginDialog.close(success);
      loginDialog = null;
    }
  }

  function onLoginDialogClose(success) {
    if ( success ) {
      queue.retryAll();
    } else {
      queue.cancelAll();
      redirect();
    }
  }

  queue.onItemAdded = function() {
    if ( queue.hasMore() ) {
      service.showLogin();
    }
  };

  var service = {

    //////////////////////////////////////////////////////////////////////////////////////////
    // The following methods provide information you can bind to in the UI

    // Get the first reason for needing a login
    getLoginReason: function() {
      return queue.retryReason();
    },


    //////////////////////////////////////////////////////////////////////////////////////////
    // The following methods provide handlers for actions that could be triggered in the UI

    // Show the modal login dialog
    showLogin: function() {
      openLoginDialog();
    },

    // Attempt to authenticate a user by the given name and password
    login: function(username, password) {
      var url = "http://" + $rootScope.config.host + ":" + $rootScope.config.port + "/login";
      //var request = $http.post(url, {username: username, password: password});
      var request = $http({
          method: 'POST',
          url: url,
          //withCredentials: true,
          headers: {'Content-Type':'application/json'},
          data: {
            'username': username,
            'password': password
          }

      });
      return request.then(function(response) {
        console.debug("login user " + response.data.user);
        currentUser.update(response.data.user);
        if ( currentUser.isAuthenticated() ) {
          console.log("user authentificate");
          closeLoginDialog(true);
          $rootScope.$broadcast('userLogon', currentUser);
        }
      });
    },

    cancelLogin: function() {
      closeLoginDialog(false);
      redirect();
    },

    // Logout the current user
    logout: function(redirectTo) {
      var url = "http://" + $rootScope.config.host + ":" + $rootScope.config.port + "/logout";
      var request = $http({
          method: 'POST',
          url: url,
          //withCredentials: true,
          headers: {'Content-Type':'application/json'},
          data: {
            'username': currentUser.username,
            'password': currentUser.password
          }
      });

      request.then(function() {
        //broadcat for the other to notify disconnection , used for send user:left message to the server 
        $rootScope.$broadcast('userLogout', currentUser);
        currentUser.clear();
       
        redirect(redirectTo);
      });
    },

    //////////////////////////////////////////////////////////////////////////////////////////
    // The following methods support AngularJS routes.
    // You can add them as resolves to routes to require authorization levels before allowing
    // a route change to complete

    // Require that there is an authenticated user
    // (use this in a route resolve to prevent non-authenticated users from entering that route)
    requireAuthenticatedUser: function() {
      var promise = service.requestCurrentUser().then(function(currentUser) {
        if ( !currentUser.isAuthenticated() ) {
          return queue.pushRetryFn('unauthenticated-client', service.requireAuthenticatedUser);
        }
      });
      return promise;
    },

    // Require that there is an administrator logged in
    // (use this in a route resolve to prevent non-administrators from entering that route)
    requireAdminUser: function() {
      var promise = service.requestCurrentUser().then(function(currentUser) {
        if ( !currentUser.isAdmin() ) {
          return queue.pushRetryFn('unauthorized-client', service.requireAdminUser);
        }
      });
      return promise;
    },

    // Ask the backend to see if a user is already authenticated - this may be from a previous session.
    requestCurrentUser: function() {
      if ( currentUser.isAuthenticated() ) {
        console.log("user requestCurrentUser isAuthenticated");
        return $q.when(currentUser);
      } else {
        var url = "http://" + $rootScope.config.host + ":" + $rootScope.config.port + '/current-user';
        console.debug("request the current user from the address : " + url);
        return $http.get(url).then(function(response) {
          console.log("user requestCurrentUser $http.get : " + response.data.user);
          currentUser.update(response.data.user);
          $rootScope.$broadcast('userLogon', currentUser);
          return currentUser;
        });
      }
    }
  };
  return service;
}]);