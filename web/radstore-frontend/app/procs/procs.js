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
  $scope.result = {};
  $scope.running = {};
  $scope.executions = {};

  $scope.runProc = function(id) {
    if(!$scope.executions[id]) 
      $scope.executions[id] = [];
    var exec = {};
    exec.running = true;        
    exec.params = [];
    for(var k in $scope.params[id]) {
      exec.params.push({name: k, value: $scope.params[id][k]});
    }
    $scope.executions[id].push(exec);

    $http.post('http://localhost:8080/api/v1/procs/'+id, $scope.params[id])
    .success(function(data) {
      exec.running = false;
      exec.result = data.status;
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
