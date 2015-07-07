'use strict';

var app = angular.module('QueryApp', []);
var api_url = 'http://52.24.67.166:3003/api/v1';

app.controller('QueryCtrl', function($scope, $http, $rootScope) {

  $('#date-from').datetimepicker();
  $('#date-to').datetimepicker();            

  $scope.current_filter = {variable: "dBZ", format: "vol"}
  $scope.api_url = $rootScope.api_url;

  $scope.prevPage = function() {
    if($scope.results.offset > 10) {
      $scope.results.offset -= 10;
      $scope.updateResults();
    }
  };

  $scope.nextPage = function() {
    if($scope.results.offset < $scope.results.count - 10) {
      $scope.results.offset += 10;
      $scope.updateResults();
    }
  };

  $scope.runQueryCrudo = function() {    
    $scope.updateResults();
  }

  $scope.updateResults = function() {
    var flt = {};
    flt['variable'] = $scope.current_filter.variable;
    flt['type'] = $scope.current_filter.format;
    flt['datetime.$gte'] = $('#date-from').data('DateTimePicker').viewDate().toJSON();
    flt['datetime.$lte'] = $('#date-to').data('DateTimePicker').viewDate().toJSON();
    flt['limit'] = 10;    
    flt['offset'] = ($scope.results) ? $scope.results.offset : 0;
    if($scope.current_filter.slice && flt['type'] != 'vol') {
      flt['slice'] = $scope.current_filter.slice;
    }
    
    $http.get(api_url+'/products', {params: flt})
      .success(function(data) {
        if(!$scope.results) {
          $scope.results = {};
        }
        $scope.results.header = ["fecha/hora","nombre archivo"];
        $scope.results.offset = data.data.offset;
        $scope.results.count = data.data.count;
        $scope.results.data = data.data.products.map(function(prod) {
          return {
            "fecha/hora": moment(prod.datetime).format("DD/MM/YYYY HH:mm:ss"), 
            "nombre archivo": prod.name,
            "href": api_url+"/products/"+prod._id+"/content"
          };
        });
      });
  };

});
