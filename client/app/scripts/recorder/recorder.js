angular.module('recorder', ['ui.bootstrap'])

.config(['$routeProvider',
    function($routeProvider) {
        $routeProvider.when('/recorder', {
            templateUrl: 'scripts/recorder/paramsList.tpl.html',
            controller: 'ParamsCtrl'

        });
    }
])

.controller('ParamsCtrl', ['$rootScope', '$scope', '$http', '$templateCache', '$dialog', 'recorderService',
    function($rootScope, $scope, $http, $templateCache, $dialog, recorderService) {
        $scope.numbers = [];
        $scope.recordAll = {};

        var editNumberDlgOpts = {
            controller: 'EditNumberCtrl',
            templateUrl: 'scripts/recorder/numberEdit.tpl.html'
        };

        var removeNumberDlgOpts = {
            controller: 'RemoveNumberCtrl',
            templateUrl: 'scripts/recorder/numberRemove.tpl.html'
        };

        var addNumberDlgOpts = {
            controller: 'AddNumberCtrl',
            templateUrl: 'scripts/recorder/numberAdd.tpl.html'
        };

        $scope.listNumbers = function() {
            recorderService.getNumbers(function(status, numbers) {
                $scope.numbers = angular.copy(numbers);
                angular.forEach($scope.numbers, function(number, keyNumber) {
                    if (number.recorded == '0') {
                        number.recorded = "0";
                    } else {
                        number.recorded = "1";
                    }
                });
            });
        }

        $scope.getSettings = function() {
            recorderService.getSettings(function(status, settings) {
                //
                console.log(" scope.getSettings : " + JSON.stringify(settings));
                $scope.settings = angular.copy(settings);
                angular.forEach(settings, function(setting, keySettings) {
                    if (setting.variable == 'RECORD_ALL') {
                        $scope.recordAll = angular.copy(setting);
                    }
                });
                console.log("$scope.settings : " + JSON.stringify($scope.settings));
            });
        }

        $scope.edit = function(number) {
            var numberToEdit = number;
            console.log("numberToEdit : " + JSON.stringify(numberToEdit) + " number " + JSON.stringify(number));

            $dialog.dialog(angular.extend(editNumberDlgOpts, {
                resolve: {
                    numberToEdit: function() {
                        return angular.copy(number);
                    }
                }
            })).open().then(function(result) {
                if (result) {
                    angular.copy(result, numberToEdit);
                    recorderService.updateNumber(numberToEdit, function(status) {
                        numberToEdit = undefined;
                        $scope.listNumbers();

                    });
                    console.log("update number : " + JSON.stringify(numberToEdit) + " result " + JSON.stringify(result));
                } else {
                    numberToEdit = undefined;
                }
            });

        };


        $scope.remove = function(number) {
            var numberToRemove = number;

            $dialog.dialog(angular.extend(removeNumberDlgOpts, {
                resolve: {
                    numberToRemove: function() {
                        return angular.copy(numberToRemove);
                    }
                }
            })).open().then(function(result) {
                console.log("$scope.remove : " + JSON.stringify(result));
                if (result != undefined && result.id != undefined) {
                    recorderService.deleteNumber(numberToRemove, function(status) {
                        numberToRemove = undefined;
                        $scope.listNumbers();

                    });
                } else {
                    numberToRemove = undefined;
                }

            });

        };

        $scope.addNumber = function() {
            var numberToAdd = {
                id: -1,
                number: "",
                comments: "",
                recorded: $scope.recordAll.value
            };
            $dialog.dialog(angular.extend(addNumberDlgOpts, {
                resolve: {
                    numberToAdd: function() {
                        return angular.copy(numberToAdd);
                    }
                }
            })).open().then(function(result) {
                if (result) {
                    angular.copy(result, numberToAdd);
                    recorderService.addNumber(numberToAdd, function(status) {
                        numberToAdd = undefined;
                        $scope.listNumbers();

                    });

                } else {
                    numberToAdd = undefined;
                }
            });

        }

        $scope.changeRecordAll = function() {
            console.log("$scope.onChangeRecordAll " + JSON.stringify($scope.recordAll));
            recorderService.updateSetting($scope.recordAll, function(status) {
                $scope.getSettings();

            });
        }

        $scope.getSettings();
        $scope.listNumbers();

    }
])
//
.controller('EditNumberCtrl', ['$rootScope', '$scope', 'dialog', 'numberToEdit',
    function($rootScope, $scope, dialog, numberToEdit) {

        $scope.numberToEdit = numberToEdit;

        $scope.save = function(user) {
            dialog.close($scope.numberToEdit);
        }

        $scope.close = function() {
            dialog.close(undefined);
        }


    }
])

//
.controller('RemoveNumberCtrl', ['$rootScope', '$scope', 'dialog', 'numberToRemove',
    function($rootScope, $scope, dialog, numberToRemove) {

        $scope.numberToRemove = numberToRemove;

        $scope.remove = function(number) {
            console.log('RemoveNumberCtrl called remove' + JSON.stringify(number));
            dialog.close(number);
        }

        $scope.close = function() {
            console.log('RemoveNumberCtrl called close');
            dialog.close(undefined);
        }

    }
])

//
.controller('AddNumberCtrl', ['$rootScope', '$scope', 'dialog', 'numberToAdd',
    function($rootScope, $scope, dialog, numberToAdd) {
        $scope.numberToAdd = numberToAdd;

        $scope.add = function() {
            dialog.close($scope.numberToAdd);
        }

        $scope.close = function(result) {
            dialog.close(undefined);
        };

    }
]);