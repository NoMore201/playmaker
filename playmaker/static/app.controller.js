angular.module('playmaker').controller('notify', [
  '$scope',
  'global',
  function($scope, global) {
    $scope.alerts = [];

    $scope.closeAlert = function(index) {
      $scope.alerts.splice(index, 1);
    };

    global.addAlert = function(type, msg) {
      newAlert = {
        type: type,
        msg: msg
      };
      $scope.alerts.push(newAlert);
    };
  }]);

angular.module('playmaker').controller('navbar', [
  '$location',
  '$scope',
  '$rootScope',
  function($location, $scope, $rootScope) {
    $rootScope.$on('$routeChangeSuccess', function() {
      $scope.path = $location.path();
    });
  }]);
