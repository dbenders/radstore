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

.controller('ProductsCtrl', function($scope, $http, $rootScope) {

  $scope.add_filter = function(typ,attr) {
    $http.get($rootScope.api_url+'/product_types/'+typ, 
      {params: {distinct: attr}})
    .success(function(data) {
      $scope.filters.push({
        name: attr, 
        options: data.data.values.map(function(x){return {value:x,name:x}})
      });
    });
  }

  $scope.type_changed = function() {
      $scope.filters = [];
      $scope.current_filter = {};
      var typ = $scope.type_filter.value;
      $http.get($rootScope.api_url+'/product_types/'+typ)
      .success(function(data){
        if(data.data.product_type.metadata) {
          for(var fld in data.data.product_type.metadata) {
            $scope.add_filter(typ,fld);
          }
        }
      });
      $scope.changed();
  }

  $scope.changed = function() {
  
    $scope.transformations = {};
    var flt = {};
    for(var k in $scope.current_filter)
      if($scope.current_filter[k].length > 0) 
        flt[k] = $scope.current_filter[k];
    flt.type = $scope.type_filter.value;

    $http.get($rootScope.api_url+'/products', 
        {params: flt})
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

        /*
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
        */
      }
      $scope.products = data.data.products;
      $scope.product_count = data.data.count;
    });
  };

  $http.get($rootScope.api_url+'/product_types/vol', 
    {params: {distinct: 'type'}})
  .success(function(data) {
    $scope.type_filter = {
      name: 'type',
      value: null,
      options: data.data.values.map(function(x){return {value:x,name:x}})
    };
  });

  $scope.api_url = $rootScope.api_url;

  /*
  $scope.filters = [];
  $scope.current_filter = {};

  $scope.add_filter('vol','type');
  $scope.add_filter('vol','variable');
  */
})



.controller('ProductCtrl', function($scope, $http, $routeParams) {
  $http.get($rootScope.api_url+'/products/'+$routeParams.id)
  .success(function(data) {
    $scope.attributes = [];
    for(var k in data.data.product) {
        $scope.attributes.push(k);
    }
    $scope.product = data.data.product;
  });

});

