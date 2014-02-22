angular.module('modulesinfo', [], ['$routeProvider', function($routeProvider){
  $routeProvider.when('/modules', {
    
    templateUrl:'scripts/modulesinfo/list.tpl.html',
    controller:'ModulesInfoListCtrl'
    /*resolve:{
      projectInfos:['ModulesInfos', function(Modules){
        return Modules.all();
      }]
    }*/
  });
}]);

angular.module('modulesinfo').controller('ModulesInfoListCtrl', ['$scope', function($scope){
  $scope.modules = {};
}]);
