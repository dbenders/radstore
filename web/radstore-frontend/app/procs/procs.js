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

.controller('ProcsCtrl', function($scope, $http, $rootScope) {

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

    $http.post($rootScope.api_url+'/procs/'+id, $scope.params[id])
    .success(function(data) {
      exec.running = false;
      exec.result = data.status;
    })
    .error(function(data) {
      exec.running = false;
      exec.result = "error";
    });
  };

  $http.get($rootScope.api_url+'/procs')
  .success(function(data) {
    console.log(data);    
    $scope.procs = data.data.processes;
  });
})



.controller('ProcCtrl', function($scope, $http, $routeParams, $rootScope) {

  $http.get($rootScope.api_url+'/procs/'+$routeParams.id)
  .success(function(data) {
    $scope.proc = data.data.process;
  });

});

