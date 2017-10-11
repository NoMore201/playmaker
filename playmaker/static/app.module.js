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
      otherwise('/');
  }

]).run(['$rootScope', '$location', '$http', 'global',
  function ($rootScope, $location, $http, global) {

    $http({
      method: 'POST',
      url: '/api/login',
      data: '{}'
    }).then(function success(response) {
        if (response.data.message === 'YES') {
          global.auth.login();
          $location.path('/');
        }
        else {
          $location.path('/login');
        }
      }, function error(response) {
      });

    $rootScope.$on('$routeChangeStart', function (event, next, current) {

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

    });
}]);


app.component('appList', {
  templateUrl: '/views/app.html',
  controller: function AppController(api, global) {
    var ctrl = this;

    ctrl.apps = [];
    ctrl.updatingState = false;
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
        app.version = data.message.success[0].versionCode;
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
      global.addAlert('info', 'Updating fdroid repository');
      api.fdroid(function (data) {
        if (data === 'err') {
          global.addAlert('danger', 'Error updating repository');
          return;
        }
        if (data.status === 'PENDING') {
          global.addAlert('warning', 'Update process still running');
          return;
        }
        if (data.status === 'SUCCESS') {
          global.addAlert('success', 'Fdroid repository updated succesfully');
        }
      });
    };

    api.getApps(function(data) {
      if (data.status === 'PENDING') {
        ctrl.updatingState = true;
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

      var plaintext = user.email + '\x00' + user.password;
      var plaintextHash = CryptoJS.SHA256(plaintext);
      //using sha256(message) as key
      var iv = CryptoJS.lib.WordArray.random(16);
      var encrypted = CryptoJS.AES.encrypt(plaintext, plaintextHash, {
        iv: iv,
        mode: CryptoJS.mode.CBC
      });
      iv.concat(encrypted.ciphertext)
      var ciphertext = CryptoJS.enc.Base64.stringify(iv);
      var hashToB64 = CryptoJS.enc.Base64.stringify(plaintextHash);

      api.login(ciphertext, hashToB64, function(data) {
        if (data.status === 'ERROR') {
          global.addAlert('danger', data.message);
          ctrl.loggingIn = false;
          return;
        }
        global.auth.login();
        $location.path('/');
        ctrl.loggingIn = false;
      });
    }
  }
});
