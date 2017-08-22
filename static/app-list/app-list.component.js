angular.
  module('appList').
  component('appList', {
    template: '<ul><li ng-repeat="app in $ctrl.apps">{{app}}</li></ul>',
    controller: ['$routeParams',
      function AppController($routeParams) {
        this.apps = ['tizio', 'caio'];
      }
    ]
  });
