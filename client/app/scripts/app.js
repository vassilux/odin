'use strict';
// Declare app level module which depends on filters, and services
angular.module('app', ['ui.directives', 'localization', 'ui.bootstrap', 'ui.bootstrap.collapse', 'plunker',
  'app.filters',
  'app.services',
  'app.directives',
  'modulesinfo',
  'dashboard',
  'dashboard.services',
  'peers',
  'peers.services',
  'calls',
  'calls.services',
  'services.breadcrumbs',
  'users',
  'users.services',
  'authentication',
  'services.i18nNotifications',
  'services.localizedMessages'
])
  .config(['$routeProvider',
    function($routeProvider) {
      //I try to reconfigure CROS domain for Firefox
      //$httpProvider.defaults.useXDomain = true;
      //delete $httpProvider.defaults.headers.common['X-Requested-With'];
      //delete $httpProvider.defaults.headers.post['Content-Type'];  
      return $routeProvider
        .when('/', {
          template: '<div></div>',
          controller: 'AppCtrl',
          resolve: {
            //Invoque configurationService to load config.json file from server before initialize AppCtrl
            //AppCtrl initialise rootScope variable config
            configuration: (['configurationService',
              function(configurationService) {
                console.log("app routeProvider configuration for / route");
                return configurationService.promise;
              }
            ])
          }
        })
        .otherwise({
          redirectTo: '/dashboard'
        });

    }
  ])
  .config(['$locationProvider',
    function($locationProvider) {
      return $locationProvider.html5Mode(true); //.hashPrefix("#");
    }
  ])
  .run(function($rootScope, $location, currentUser) {
    // register listener to watch route changes
    $rootScope.$on("$routeChangeStart", function(event, next, current) {
      if (currentUser.userInfo == null) {
        // no logged user or the page relaoded with F5 
        $location.path("/");

      }
    });
  });