angular.module('users.services',[])

.factory('usersCrudService', ['$rootScope', '$http', 'currentUser', function($rootScope, $http, currentUser) {
  console.log("Create usersCrudService");
  var usersCrudService = {};

  usersCrudService.getUsers = function(callback) {
    var url = "http://" + $rootScope.config.host + ":" + $rootScope.config.port + "/api/users";
     $http({
      method: 'GET',
      url: url
    }).
    success(function(data, status, headers, config) {
      callback(status, data)
      //$scope.users = data; //set view model
      //$scope.view = './Partials/list.html'; //set to list view
    }).
    error(function(data, status, headers, config) {
      callback(status, data);
      //$scope.users = data;
      // $scope.view = './Partials/list.html';
    });
  };

  usersCrudService.deleteUser = function(user, callback) {
    var url = "http://" + $rootScope.config.host + ":" + $rootScope.config.port + "/api/users/";
  	console.log(" usersCrudService.deleteUser " + user.username);
     $http({
      method: 'DELETE',
      url: url + user.username
    }).
    success(function(data, status, headers, config) {
      callback(status)
      //$scope.users = data; //set view model
      //$scope.view = './Partials/list.html'; //set to list view
    }).
    error(function(data, status, headers, config) {
    	console.log(" usersCrudService.deleteUser " + user.username + " error");
      callback(status);
      //$scope.users = data;
      // $scope.view = './Partials/list.html';
    });
  };

  usersCrudService.addUser = function(user, callback) {
  	console.log(" usersCrudService.addUser " + JSON.stringify(user));
    var url = "http://" + $rootScope.config.host + ":" + $rootScope.config.port + "/api/users/";
  	var xsrf = $.param({firstName: user.firstName, lastName: user.lastName, username: user.username,  password : user.password, admin: user.admin});
     $http({
      method: 'POST',
      url: url,
      data: xsrf,
      headers: {'Content-Type': 'application/x-www-form-urlencoded'}
    }).
    success(function(data, status, headers, config) {
      callback(status)
      //$scope.users = data; //set view model
      //$scope.view = './Partials/list.html'; //set to list view
    }).
    error(function(data, status, headers, config) {
    	console.log(" usersCrudService.addUser " + user.username + " error");
      callback(status);
      //$scope.users = data;
      // $scope.view = './Partials/list.html';
    });
  };

  usersCrudService.updateUser = function(user, callback) {
    console.log(" usersCrudService.updateUser " + JSON.stringify(user));
    var url = "http://" + $rootScope.config.host + ":" + $rootScope.config.port + "/api/users/";
    var xsrf = $.param({firstName: user.firstName, lastName: user.lastName, 
      username: user.username,  password : user.password, admin: user.admin});
     $http({
      method: 'PUT',
      url: url + user.firstName,
      data: xsrf,
      headers: {'Content-Type': 'application/x-www-form-urlencoded'}
    }).
    success(function(data, status, headers, config) {
      callback(status)
    }).
    error(function(data, status, headers, config) {
      console.log(" usersCrudService.updateUser " + user.username + " error");
      callback(status);
    });
  };


  return usersCrudService;

}]);