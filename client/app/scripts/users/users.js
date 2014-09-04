angular.module('users', ['ui.bootstrap'])

.config(['$routeProvider', function($routeProvider) {
  $routeProvider.when('/users', {
    templateUrl: 'scripts/users/usersList.tpl.html',
    controller: 'UsersCtrl'

  });
}])

.controller('UsersCtrl', ['$rootScope', '$scope', '$http', '$templateCache', '$dialog', 'usersCrudService',
  function($rootScope, $scope, $http, $templateCache, $dialog, usersCrudService) {
  $scope.users = [];

  var editUserDlgOpts = {
    controller: 'EditUserCtrl',
    templateUrl: 'scripts/users/userEdit.tpl.html'
  };

  var removeUserDlgOpts = {
    controller: 'RemoveUserCtrl',
    templateUrl: 'scripts/users/userRemove.tpl.html'
  };

  var addUserDlgOpts = {
    controller: 'AddUserCtrl',
    templateUrl: 'scripts/users/userAdd.tpl.html'
  };


  $scope.listUsers = function() {
    usersCrudService.getUsers(function(status, users){
      //console.log("Users : " + JSON.stringify(users));
      //angular.copy($scope.users, users);  
      $scope.users = users
    });
   
  }

  $scope.editUser = function(user) {
    var userToEdit = user;

    $dialog.dialog(angular.extend(editUserDlgOpts, {
      resolve: {
        userToEdit: function() {
          return angular.copy(userToEdit);
        }
      }
    })).open().then(function(result) {
      if(result) {
        //console.log("Users edit result: " + JSON.stringify(result));
        angular.copy(result, userToEdit);
        userToEdit.admin = result.admin;
        usersCrudService.updateUser(userToEdit, function(status){
          userToEdit = undefined;
          $scope.listUsers();

        });
        //console.log("update user : " + JSON.stringify(userToEdit) + " result " + JSON.stringify(result));
      }else{
        userToEdit = undefined;
      }
    });
  };


$scope.removeUser = function(user) {
  var userToRemove = user;

    $dialog.dialog(angular.extend(removeUserDlgOpts, {
      resolve: {
        userToRemove: function() {
          return angular.copy(userToRemove);
        }
      }
    })).open().then(function(result) {
      console.log("[removeuser]" + result);
      if(result == 'ok') {
        usersCrudService.deleteUser(userToRemove, function(status){
          userToRemove = undefined;
          $scope.listUsers();

        });
      }else{
        userToRemove = undefined;
      }

    });
}

$scope.addNewUser = function() {
  var userToAdd = {username: "", lastName: "", firstName: "", password: "", admin: false};
  //
  $dialog.dialog(angular.extend(addUserDlgOpts, {
    resolve: {
      userToAdd: function() {
        return angular.copy(userToAdd);
      }
    }
  })).open().then(function(result) {
    if(result) {
      angular.copy(result, userToAdd);
      usersCrudService.addUser(userToAdd, function(status){
          userToAdd = undefined;
          $scope.listUsers();

        });
      //console.log("add user : " + JSON.stringify(userToAdd) + " result " + JSON.stringify(result));
      //angular.copy(result, userToRemove);
    }else{
      userToAdd = undefined;
    }
    
  });
   
    
}

$scope.listUsers();

}])
//dialog and userToEdit injected by UsersCtrl
.controller('EditUserCtrl', ['$rootScope', '$scope', 'dialog', 'userToEdit' , function($rootScope, $scope, dialog, userToEdit ) {

  $scope.userToEdit = userToEdit;
  console.log("User to edit : " + JSON.stringify(userToEdit));

  $scope.saveUser = function(user) {
    dialog.close($scope.userToEdit);
  }

  $scope.closeEditUser=function(){
    dialog.close(undefined);
  }


}])

//dialog and userToRemove injected by UsersCtrl
.controller('RemoveUserCtrl', ['$rootScope', '$scope', 'dialog', 'userToRemove' , function($rootScope, $scope, dialog, userToRemove ) {
  $scope.userToRemove = userToRemove;
  $scope.close = function(result){
    dialog.close(result);
  };

}])

//dialog and userToAdd injected by UsersCtrl
.controller('AddUserCtrl', ['$rootScope', '$scope', 'dialog', 'userToAdd' , function($rootScope, $scope, dialog, userToAdd ) {
  $scope.userToAdd = userToAdd;

  $scope.addUser=function(){
    dialog.close($scope.userToAdd);
  }

  $scope.close = function(result){
    dialog.close(undefined);
  };

}]);
