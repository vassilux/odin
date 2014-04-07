angular.module('recorder.services',[])

.factory('recorderService', ['$rootScope', '$http', function($rootScope, $http) {
  console.log("**** Create recorderService **** ");
  var recorderService = {};

  recorderService.getNumbers = function(callback) {
    var url = "http://" + $rootScope.config.host + ":" + $rootScope.config.port + "/rc1/recordNumbers/";
     $http({
      method: 'GET',
      url: url
    }).
    success(function(data, status, headers, config) {
      callback(status, data)
    }).
    error(function(data, status, headers, config) {
      callback(status, data);
    });
  };

  recorderService.deleteNumber = function(number, callback) {
    var url = "http://" + $rootScope.config.host + ":" + $rootScope.config.port + "/rc1/recordNumbers/";
     $http({
      method: 'DELETE',
      url: url + number.id
    }).
    success(function(data, status, headers, config) {
      callback(status)
    }).
    error(function(data, status, headers, config) {
    	console.log(" recorderService.deleteNumber " + number.id + " error");
      callback(status);

    });
  };

  recorderService.addNumber = function(number, callback) {
  	console.log(" recorderService.addNumber " + JSON.stringify(number));
    var url = "http://" + $rootScope.config.host + ":" + $rootScope.config.port + "/rc1/recordNumbers";
  	var xsrf = $.param({number: number.number, comments: number.comments,  recorded : number.recorded});
     $http({
      method: 'POST',
      url: url,
      data: xsrf,
      headers: {'Content-Type': 'application/x-www-form-urlencoded'}
    }).
    success(function(data, status, headers, config) {
      callback(status)

    }).
    error(function(data, status, headers, config) {
    	console.log(" recorderService.addUser " + user.username + " error");
      callback(status);

    });
  };

  recorderService.updateNumber = function(number, callback) {
    console.log(" recorderService.updateNumber " + JSON.stringify(number));
    var url = "http://" + $rootScope.config.host + ":" + $rootScope.config.port + "/rc1/recordNumbers/";
    var xsrf = $.param({id: number.id, number: number.number, comments: number.comments,  recorded : number.recorded});
     $http({
      method: 'POST',
      url: url,
      data: xsrf,
      headers: {'Content-Type': 'application/x-www-form-urlencoded'}
    }).
    success(function(data, status, headers, config) {
      callback(status)
    }).
    error(function(data, status, headers, config) {
      console.log(" recorderService.updateNumber " + number.number + " error");
      callback(status);
    });
  };

  //
  recorderService.getSettings = function(callback) {
    var url = "http://" + $rootScope.config.host + ":" + $rootScope.config.port + "/rc1/settings/";
     $http({
      method: 'GET',
      url: url
    }).
    success(function(data, status, headers, config) {
      callback(status, data)
    }).
    error(function(data, status, headers, config) {
      callback(status, data);
    });
  };

  recorderService.updateSetting = function(setting, callback) {
    console.log(" recorderService.updateSetting " + JSON.stringify(setting));
    var url = "http://" + $rootScope.config.host + ":" + $rootScope.config.port + "/rc1/settings/";
    var xsrf = $.param({id: setting.id, variable: setting.variable, value: setting.value});
     $http({
      method: 'POST',
      url: url,
      data: xsrf,
      headers: {'Content-Type': 'application/x-www-form-urlencoded'}
    }).
    success(function(data, status, headers, config) {
      callback(status)
    }).
    error(function(data, status, headers, config) {
      console.log(" recorderService.updateSetting " + setting.id + " " + "setting.variable" + "error");
      callback(status);
    });
  };

  return recorderService;

}]);