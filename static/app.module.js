var app = angular.module('playmaker', [
  'ngRoute'
]);

app.controller('navbar', [
  '$location',
  '$scope', 
  '$rootScope',
  function($location, $scope, $rootScope) {
    $rootScope.$on('$routeChangeSuccess', function() {
      $scope.path = $location.path();
      console.log($scope.path);
    });
  }]);

app.config(['$locationProvider', '$routeProvider',
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

app.service('api', ['$http', function($http) {

  this.getApps = function(callback) {
    $http({
      method: 'GET',
      url: '/api/apps'
    }).then(function success(response) {
      callback(response.data);
    }, function error(response) {
      callback(response.data);
    });
  };

  this.search = function(app, callback) {
    $http({
      method: 'GET',
      url: '/api/search?search=' + app
    }).then(function success(response) {
      callback(response.data);
    }, function error(response) {
      callback(response.data);
    });
  };

  this.check = function(callback) {
    $http.post('/api/check')
      .then(function success(response) {
        callback(response.data);
      }, function error(response) {
        callback(response.data);
      });
  };

  this.remove = function(value, callback) {
    var requestData = {
      delete: value
    };
    $http({
      method: 'DELETE',
      url: '/api/delete',
      data: JSON.stringify(requestData)
    }).then(function success(response) {
        callback(response.data);
      }, function error(response) {
        callback(response.data);
      });
  };

}]);

app.component('appList', {
  templateUrl: '/views/app.html',
  controller: function AppController($routeParams, api) {
    var ctrl = this;

    ctrl.check = function() {
      api.check(function(data) {
        data.forEach(function(a) {
          var oldApp = ctrl.apps.find(function(elem) {
            return elem.docId === a.docId;
          });
          if (oldApp === undefined) return;
          oldApp.needsUpdate = true;
        });
      });
    };

    ctrl.updateApp = function(app) {
      //TODO: implement
    };

    ctrl.delete = function(app) {
      api.remove(app.docId, function(data) {
        if (data === 'OK') {
          ctrl.apps.splice(app);
        }
      });
    };

    api.getApps(function(data) {
      var apps = data;
      apps.forEach(function(a) {
        a.updating = false;
        a.needsUpdate = false;
      });
      ctrl.apps = apps;
    });
  }
});

app.directive('onEnter', function() {
  return function(scope, element, attrs) {
    element.bind("keydown keypress", function (event) {
      if(event.which === 13) {
        scope.$apply(function (){
          scope.$eval(attrs.onEnter);
        });

        event.preventDefault();
      }
    });
  };
});

app.component('searchView', {
  templateUrl: '/views/search.html',
  controller: function SearchController($routeParams, api) {
    var ctrl = this;
    ctrl.results = [];

    ctrl.search = function(app) {
      if (app === undefined) return;
      api.search(app, function(data) {
        console.log(data);
        ctrl.results = data;
      });
    };
  }
});
