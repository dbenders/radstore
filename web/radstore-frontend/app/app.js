'use strict';

// Declare app level module which depends on views, and components
angular.module('myApp', [
  'ngRoute',
  'myApp.products',
  'myApp.procs',
  'myApp.version'
]).
run(function($rootScope) {
    $rootScope.api_url = 'http://52.24.67.166:3003/api/v1';
}).
config(['$routeProvider', function($routeProvider) {
  $routeProvider.otherwise({redirectTo: '/products'});
}]);
