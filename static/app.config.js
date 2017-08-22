angular.
  module('playmaker').
  config(['$locationProvider', '$routeProvider',
    function config($locationProvider, $routeProvider) {
      $locationProvider.hashPrefix('!');

      $routeProvider.
        when('/', {
          template: '<app-list></app-list>'
        }).
        when('/search', {
          template: '<search-view></search-view>'
        }).
        otherwise('/');
    }
  ]);
