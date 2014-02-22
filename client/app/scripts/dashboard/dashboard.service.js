angular.module('dashboard.services',[])

.factory('dashboardSysInfoService', ['$rootScope', '$http', function($rootScope, $http) {
  console.log("Create dashboardSysInfoService");
  var dashboardSysInfoService = {};

  dashboardSysInfoService.getSysInfo = function(callback) {
    var url = "http://" + $rootScope.config.host + ":" + $rootScope.config.port + "/sysinfo";
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
  //
  return dashboardSysInfoService;

}]);