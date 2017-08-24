var app = angular.module('playmaker', [
  'ngRoute',
  'ui.bootstrap'
]);

app.controller('navbar', [
  '$location',
  '$scope',
  '$rootScope',
  function($location, $scope, $rootScope) {
    $rootScope.$on('$routeChangeSuccess', function() {
      $scope.path = $location.path();
    });
  }]);

app.service('global', function() {
  this.addAlert = {};

  this.desktop = false;
  this.mobile = false;

  var screenWidth = window.innerWidth;
  if (screenWidth < 700) {
    this.mobile = true;
  } else {
    this.desktop = true
  }

});

app.controller('notify', [
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

  this.download = function(app, callback) {
    var requestData = {
      download: [app]
    };
    $http({
      method: 'POST',
      url: '/api/download',
      data: JSON.stringify(requestData)
    }).then(function success(response) {
        callback(response.data);
      }, function error(response) {
        callback(response.data);
      });
  };

  this.remove = function(app, callback) {
    var requestData = {
      delete: app
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
  controller: function AppController($routeParams, api, global) {
    var ctrl = this;

    ctrl.check = function() {
      global.addAlert('info', 'Checking for updates');
      api.check(function(data) {
        if (data.length === 0) {
          global.addAlert('success', 'All apps are up-to-date!');
        }
        if (data.length > 0) {
          global.addAlert('info', data.length.toString() + ' apps must be updated');

          data.forEach(function(a) {
            var oldApp = ctrl.apps.find(function(elem) {
              return elem.docId === a.docId;
            });
            if (oldApp === undefined) return;
            oldApp.needsUpdate = true;
          });
        }
      });
    };

    ctrl.downloadApp = function(app) {
      api.download(app.docId, function(data) {
        if (data.success.length === 0) return;
        newApp = data.success[0];
      });
    };

    ctrl.updateApp = function(app) {
      app.needsUpdate = false;
      app.updating = true;
      api.download(app.docId, function(data) {
        if (data.success.length === 0) return;
        newApp = data.success[0];
        app.version = newApp.version;
        app.updating = false;
      });
    };

    ctrl.delete = function(app) {
      api.remove(app.docId, function(data) {
        if (data === 'OK') {
          var i = ctrl.apps.findIndex(function(elem) {
            return elem.docId === app.docId;
          });
          ctrl.apps.splice(i, 1);
        } else {
          global.addAlert('danger', 'Unable to delete ' + app.docId);
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

app.controller('modalviewer', [
  '$uibModal',
  function($uibModal) {

  }]);

app.component('searchView', {
  templateUrl: '/views/search.html',
  controller: function SearchController($routeParams, $uibModal, api, global) {
    var ctrl = this;
    ctrl.desktop = global.desktop;
    ctrl.mobile = global.mobile;
    ctrl.results = [];
    ctrl.searching = false;

    ctrl.modalOpen = function (item) {
      $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'myModalContent.html',
        controller: function($scope) {
          $scope.app = item;
        }
      });
    };

    ctrl.search = function(app) {
      if (app === undefined) return;
      ctrl.results = [];
      ctrl.searching = true;
      api.search(app, function(data) {
        data.forEach(function(d) {
          d.dling = false;
          d.dled = false;
        });
        ctrl.results = data;
        ctrl.searching = false;
      });
    };

    ctrl.doNothing = function() {
      console.log('Doing nothing');
    };

    ctrl.download = function(app) {
      app.dling = true;
      api.download(app.docId, function(data) {
        if (data.success.length === 0) {
          app.dling = false;
          return;
        }
        app.dling = false;
        app.dled = true;
      });
    };
  }
});
