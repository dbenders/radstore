'use strict';

// Declare app level module which depends on views, and components
angular.module('myApp', [
  'ngRoute',
  'myApp.products',
  'myApp.procs',
  'myApp.query',
  'myApp.version',
  'ui.bootstrap'
]).
run(function($rootScope) {
    //$rootScope.api_url = 'http://52.24.67.166:3003/api/v1';
    $rootScope.api_url = 'http://localhost:3003/api/v1';
}).
config(['$routeProvider', function($routeProvider) {
  $routeProvider.otherwise({redirectTo: '/consulta'});
}]);
