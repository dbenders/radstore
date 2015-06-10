'use strict';

angular.module('myApp.procs', ['ngRoute'])

.config(['$routeProvider', function($routeProvider) {
  $routeProvider
    .when('/procs/:id', {
      templateUrl: 'procs/proc.html',
      controller: 'ProcCtrl'      
    })  
    .when('/procs', {
      templateUrl: 'procs/procs.html',
      controller: 'ProcsCtrl'
    })
}])

.controller('ProcsCtrl', function($scope, $http) {

  $scope.params = {};
  
  $scope.runProc = function(procName, transfName) {
    $http.post('http://localhost:8080/api/v1/procs/'+procName+'/'+transfName, $scope.params)
    .success(function(data) {
      window.alert(data);
    });
  };

  $http.get('http://localhost:8080/api/v1/procs')
  .success(function(data) {
    console.log(data);    
    $scope.procs = data.data.processes;
  });
})



.controller('ProcCtrl', function($scope, $http, $routeParams) {

  $http.get('http://localhost:8080/api/v1/procs/'+$routeParams.id)
  .success(function(data) {
    $scope.proc = data.data.process;
  });

});

