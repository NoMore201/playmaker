var app = angular.module('playmaker', [
  'ngRoute',
  'ui.bootstrap'
]);

app.config(['$locationProvider', '$routeProvider',
  function config($locationProvider, $routeProvider) {

    $routeProvider.
      when('/', {
        template: '<app-list></app-list>'
      }).
      when('/search', {
        template: '<search-view></search-view>'
      }).
      when('/login', {
        template: '<login-view></login-view>'
      }).
      when('/enforce', {
        template: '<enforce-view></enforce-view>'
      }).
      otherwise('/');
  }

]).run(['$rootScope', '$location', '$http', 'global',
  function ($rootScope, $location, $http, global) {
    if ($location.protocol() !== 'https' &&
        !global.forceHttp) {
      $rootScope.$apply(function () {
        $location.path('/enforce');
      });
    } else {
      $http({
        method: 'GET',
        url: '/api/apps'
      }).then(function success(response) {
          if (response.data.message.status === 'UNAUTHORIZED') {
            $location.path('/login');
          }
          else {
            global.auth.login();
            $location.path('/');
          }
        }, function error(response) {
        });
    }

    $rootScope.$on('$routeChangeStart', function (event, next, current) {
      if ($location.protocol() !== 'https' &&
          !global.forceHttp) {
        event.preventDefault();
        $location.path('/enforce');
      } else {
        if (!global.auth.isLoggedIn() &&
            $location.path() !== '/login') {
          event.preventDefault();
          $location.path('/login');
        } else if (global.auth.isLoggedIn() &&
                   $location.path() === '/login') {
          // redirect home
          event.preventDefault();
          $location.path('/');
        }
      }
    });
  }
]);

app.component('enforceView', {
  templateUrl: '/views/error.html',
  controller: function EnforceController($location, global) {
    var ctrl = this;

    ctrl.acceptEula = function(checkbox) {
      if (checkbox === undefined || !checkbox.value) {
        return;
      }
      global.forceHttp = true;
      $location.path('/login');
    };
  }
});

app.component('appList', {
  templateUrl: '/views/app.html',
  controller: function AppController(api, global) {
    var ctrl = this;

    ctrl.apps = [];
    ctrl.updatingState = false;
    ctrl.lastFdroidUpdate = 'None';
    ctrl.desktop = global.desktop;
    ctrl.mobile = global.mobile;

    ctrl.check = function() {
      global.addAlert('info', 'Checking for updates');
      api.check(function(data) {
        if (data === 'err') {
          global.addAlert('danger', 'Cannot check for updates');
          return;
        }
        if (data.status === 'SUCCESS' && data.message.length === 0) {
          global.addAlert('success', 'All apps are up-to-date!');
        }
        if (data.status === 'SUCCESS' && data.message.length > 0) {
          global.addAlert('info', data.message.length.toString() + ' apps must be updated');

          data.message.forEach(function(newApp) {
            var oldAppIndex = ctrl.apps.findIndex(function(elem) {
              return elem.docId === newApp;
            });
            if (oldAppIndex === -1) return;
            ctrl.apps[oldAppIndex].needsUpdate = true;
          });
        }
      });
    };

    ctrl.downloadApp = function(app) {
      api.download(app.docId, function(data) {
        //TODO: error handling
        if (data.message.success.length === 0) return;
      });
    };

    ctrl.updateApp = function(app) {
      app.needsUpdate = false;
      app.updating = true;
      api.download(app.docId, function(data) {
        if (data === 'err' || data.status === 'ERROR') {
          global.addAlert('danger', 'Unable to update ' + app.docId);
          app.updating = false;
          return;
        }
        if (data.message.success.length === 0) {
          global.addAlert('danger', 'Unable to update ' + app.docId);
          app.updating = false;
          return;
        }
        app.versionCode = data.message.success[0].versionCode;
        app.updating = false;
      });
    };

    ctrl.delete = function(app) {
      api.remove(app.docId, function(data) {
        if (data.status === 'SUCCESS') {
          var i = ctrl.apps.findIndex(function(elem) {
            return elem.docId === app.docId;
          });
          ctrl.apps.splice(i, 1);
        } else {
          global.addAlert('danger', 'Unable to delete ' + app.docId);
        }
      });
    };

    ctrl.fdroid = function() {
      var oldUpdate = ctrl.lastFdroidUpdate;
      ctrl.lastFdroidUpdate = 'Pending';
      api.fdroidUpdate(function (data) {
        if (data === 'err') {
          global.addAlert('danger', 'Error updating repository');
          ctrl.lastFdroidUpdate = oldUpdate;
          return;
        }
        if (data.status === 'PENDING') {
          return;
        }
        if (data.status === 'SUCCESS') {
          api.fdroid(function(data) {
            if (data.status !== 'SUCCESS') {
              return;
            }
            ctrl.lastFdroidUpdate = data.message;
          });
        }
      });
    };

    api.getApps(function(data) {
      if (data.status === 'PENDING') {
        ctrl.updatingState = true;
        return;
      }
      if (data.status === 'UNAUTHORIZED') {
        return;
      }
      ctrl.updatingState = false;
      var apps = data.message;
      apps.forEach(function(a) {
        if (ctrl.mobile && a.title.length > 21) {
          a.title = a.title.substring(0, 22) + '...';
        }
        roundedStars = Math.round(a.aggregateRating.starRating);
        a.formattedStars = a.aggregateRating.starRating.toFixed(1);
        var starList = [];
        for (i = 0; i < 5; i++) {
          if (i+1 <= roundedStars){
            starList.push({index: i, full: true});
          } else {
            starList.push({index: i, full: false});
          }
        }
        a.starList = starList;
        a.formattedSize = a.installationSize / (1024*1024);
        a.formattedSize = a.formattedSize.toFixed(2);
        a.updating = false;
        a.needsUpdate = false;
      });
      ctrl.apps = apps;
    });

    api.fdroid(function(data) {
      if (data.status !== 'SUCCESS') {
        return;
      }
      ctrl.lastFdroidUpdate = data.message;
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
  controller: function SearchController($uibModal, api, global) {
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
      // no input by the user
      if (app === undefined || app === '') return;
      ctrl.results = [];
      ctrl.searching = true;
      api.search(app, function(data) {
        if (data === 'err') {
          global.addAlert('danger', 'Error while searching');
          ctrl.searching = false;
          return;
        }
        if (data.status === 'SUCCESS' && data.message.length === 0) {
          global.addAlert('warning', 'No result for "' + app + '"');
          ctrl.searching = false;
          return;
        }
        data.message.forEach(function(d) {
          d.dling = false;
          d.dled = false;
        });
        ctrl.results = data.message;
        ctrl.searching = false;
      });
    };

    ctrl.download = function(app) {
      app.dling = true;
      api.download(app.docId, function(data) {
        if (data === 'err') {
          app.dling = false;
          global.addAlert('danger', 'Error downloading app');
          return;
        }
        if (data.status === 'SUCCESS' && data.message.success.length === 0) {
          app.dling = false;
          global.addAlert('warning', 'Cannot download ' + app.docId);
          return;
        }
        app.dling = false;
        app.dled = true;
      });
    };
  }
});

app.component('loginView', {
  templateUrl: '/views/login.html',
  controller: function LoginController($location, api, global) {
    var ctrl = this;

    ctrl.loggingIn = false;
    ctrl.badUsername = false;
    ctrl.badPassword = false;

    ctrl.login = function(user) {
      ctrl.badUsername = false;
      ctrl.badPassword = false;

      if (user.email === '' || user.email === undefined) {
        ctrl.badUsername = true;
        return;
      }

      if (user.password === '' || user.password === undefined) {
        ctrl.badPassword = true;
        return;
      }

      ctrl.loggingIn = true;

      var email = CryptoJS.enc.Utf8.parse(user.email);
      var passwd = CryptoJS.enc.Utf8.parse(user.password);
      var emailB64 = CryptoJS.enc.Base64.stringify(email);
      var passwdB64 = CryptoJS.enc.Base64.stringify(passwd);
      api.login(emailB64, passwdB64, function(data) {
        if (data.status === 'ERROR') {
          global.addAlert('danger', data.message);
          ctrl.loggingIn = false;
          return;
        }
        global.auth.login();
        $location.path('/');
        ctrl.loggingIn = false;
      });
    };
  }
});
