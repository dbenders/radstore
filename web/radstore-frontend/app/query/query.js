'use strict';

var app = angular.module('QueryApp', []);
//var api_url = 'http://52.24.67.166:3003/api/v1';
var api_url = 'http://localhost:3003/api/v1';

app.controller('QueryCtrl', function($scope, $http, $rootScope) {

  $('#date-from').datetimepicker();
  $('#date-to').datetimepicker();

  $scope.current_filter = {variable: "dBZ", format: "vol"}
  $scope.api_url = $rootScope.api_url;
  $scope.preview_src = "";

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
  };

  $scope.openPreview = function(src) {
    $scope.preview_src = src;
    $("#myModal").modal();
  };

  $scope.getDateFromPicker = function(id) {
    var d = $('#'+id).data('DateTimePicker').viewDate().toDate();
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    return d.toJSON();
  };

  $scope.updateResults = function() {
    var flt = {};
    if($scope.current_filter.variable) {
      flt['variable'] = $scope.current_filter.variable;
    }
    flt['type'] = $scope.current_filter.format;
    flt['datetime.$gte'] = $scope.getDateFromPicker('date-from');
    flt['datetime.$lte'] = $scope.getDateFromPicker('date-to');
    flt['limit'] = 10;
    flt['offset'] = ($scope.results) ? $scope.results.offset : 0;
    if($scope.current_filter.slice && flt['type'] != 'vol') {
      if($scope.current_filter.slice.substring(0,5) == 'comb_') {
        flt['type'] = flt['type'].replace('.slice','');
        var op = $scope.current_filter.slice.substring(5);
        if(op.length > 0) {
          flt['operation'] = op;
        }
      } else {
        flt['slice.num'] = $scope.current_filter.slice;
      }
    }

    $http.get(api_url+'/products', {params: flt})
      .success(function(data) {
        if(!$scope.results) {
          $scope.results = {};
        }
        $scope.results.header = ["fecha/hora"];
        if(!$scope.current_filter.variable) {
          $scope.results.header.push("variable");
        }
        if(!$scope.current_filter.slice && $scope.current_filter.format != 'vol') {
          $scope.results.header.push("elevación");
        }
        $scope.results.offset = data.data.offset;
        $scope.results.count = data.data.count;
        $scope.results.data = data.data.products.map(function(prod) {
          var ans = {
            "fecha/hora": moment(prod.datetime).format("DD/MM/YYYY HH:mm:ss"),
            "href": api_url+"/products/"+prod._id+"/content",
            "variable": prod.variable
          }
          if(prod.slice) {
            ans["elevación"] = prod.slice.posangle + "°";
          }
          if(prod.thumbnail) {
            ans.thumbnail = api_url+"/products/"+prod.thumbnail+"/content";
          } else {
            ans.thumbnail = "https://upload.wikimedia.org/wikipedia/commons/d/da/Imagen_no_disponible.svg";
          }
          return ans;
        });
      });
  };

});
