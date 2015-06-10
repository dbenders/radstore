'use strict';

angular.module('myApp.products', ['ngRoute'])

.config(['$routeProvider', function($routeProvider) {
  $routeProvider
    .when('/products/:id', {
      templateUrl: 'products/product.html',
      controller: 'ProductCtrl'      
    })  
    .when('/products', {
      templateUrl: 'products/products.html',
      controller: 'ProductsCtrl'
    })
}])

.controller('ProductsCtrl', function($scope, $http) {

  $scope.changed = function() {
  
    $scope.transformations = {};

    $http.get('http://localhost:8080/api/v1/products', 
        {params: {type: $scope.type, variable: $scope.variable}})
    .success(function(data) {

      $scope.product_attributes = [];
      for(var k in data.data.products[0]) {
        if(k != '_id' && k != 'content_length' && k != 'transformations') {
          $scope.product_attributes.push(k);
        }
      }

      var products = [];
      for(var i in data.data.products) {
        var prod = data.data.products[i];

        for(var j in prod.transformations) {
          var transf = prod.transformations[j];
          $scope.transformations[transf._id] = ['...'];
          $http.get('http://localhost:8080/api/v1/transformations/'+transf._id)
          .success(function(data) {
            if(data.data.transformation.outputs)            
              $scope.transformations[data.data.transformation._id] = 
                data.data.transformation.outputs.map(function(x){return x._id});
          });
        }
      }
      $scope.products = data.data.products;
    });
  };


  $http.get('http://localhost:8080/api/v1/product_types/vol', 
    {params: {distinct: 'variable'}})
  .success(function(data) {
    $scope.variables = data.data.values;
  });

  $http.get('http://localhost:8080/api/v1/product_types/vol', 
    {params: {distinct: 'type'}})
  .success(function(data) {
    $scope.types = data.data.values;
  });

})



.controller('ProductCtrl', function($scope, $http, $routeParams) {
  $http.get('http://localhost:8080/api/v1/products/'+$routeParams.id)
  .success(function(data) {
    $scope.attributes = [];
    for(var k in data.data.product) {
        $scope.attributes.push(k);
    }
    $scope.product = data.data.product;
  });

});

