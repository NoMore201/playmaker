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

]).run(['$rootScope', '$location', 'api', 'global',
  function ($rootScope, $location, api, global) {

    api.getApps(function(response) {
      if (response.status === 'SUCCESS') {
        global.auth.login();
      }

      if (response === 'err' || !global.auth.isLoggedIn()) {
          $location.path('/login');
      } else {
        // redirect home
        $location.path('/');
      }

      $rootScope.$on('$routeChangeStart', function (event, next, current) {
        if (!global.auth.isLoggedIn() && $location.path() !== '/login') {
          event.preventDefault();
          $location.path('/login');
        } else if (global.auth.isLoggedIn() && $location.path() === '/login') {
          // redirect home
          event.preventDefault();
          $location.path('/');
        }
      });
    });
  }
]);

app.component('appList', {
  templateUrl: '/views/app.html',
  controller: function AppController(api, global, $location) {
    var ctrl = this;

    ctrl.apps = [];
    ctrl.lastFdroidUpdate = 'None';
    ctrl.desktop = global.desktop;
    ctrl.mobile = global.mobile;
    var port = $location.port();
    ctrl.baseUrl = $location.protocol() + '://' + $location.host();
    if (port !== 80 && port !== 443) {
      ctrl.baseUrl += ":" + port.toString();
    }

    var updateApp = function(app) {
      app.updating = true;
      api.download(app, function(data) {
        if (data === 'err' || data.status === 'ERROR') {
          global.addAlert('danger', 'Unable to update ' + app.docid);
          app.updating = false;
          return;
        }
        if (data.message.success.length === 0) {
          global.addAlert('danger', 'Unable to update ' + app.docid);
          app.updating = false;
          return;
        }
        app.versionCode = data.message.success[0].versionCode;
        app.updating = false;
      });
    };

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
          global.addAlert('success', 'Updating ' + data.message.length.toString() + ' apps');

          data.message.forEach(function(newApp) {
            var oldAppIndex = ctrl.apps.findIndex(function(elem) {
              return elem.docid === newApp.docid
            });
            if (oldAppIndex === -1) return;
            updateApp(ctrl.apps[oldAppIndex]);
          });
        }
      });
    };


    ctrl.delete = function(app) {
      api.remove(app.docid, function(data) {
        if (data.status === 'SUCCESS') {
          var i = ctrl.apps.findIndex(function(elem) {
            return elem.docid === app.docid;
          });
          ctrl.apps.splice(i, 1);
        } else {
          global.addAlert('danger', 'Unable to delete ' + app.docid);
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
      if (data.status === 'UNAUTHORIZED') {
        return;
      }
      ctrl.apps = data.message.map(function(a) {
        if (a.aggregateRating !== undefined) {
          roundedStars = Math.floor(a.aggregateRating.starRating);
          a.formattedStars = a.aggregateRating.starRating.toFixed(1);
          a.starList = [];
          for (i = 0; i < 5; i++) {
            if (i+1 <= roundedStars){
              a.starList.push({index: i, full: true});
            } else {
              a.starList.push({index: i, full: false});
            }
          }
        }
        if (a.image !== undefined) {
          a.previewImage = a.image.filter(function(img) {
            return img.imageType === 4;
          });
        }
        if (a.details.appDetails.installationSize !== undefined) {
          a.formattedSize = a.details.appDetails.installationSize / (1024*1024);
          a.formattedSize = a.formattedSize.toFixed(2);
        }
        if (a.author === undefined) {
          a.author = "unknown";
        }
        if (a.files === undefined) {
          a.files = ["unknown"];
        }
        a.updating = false;
        return a;
      });
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
          d.downloading = false;
          d.disabled = false;
        });
        ctrl.results = data.message[0].child[0].child;
        ctrl.searching = false;
      });
    };

    ctrl.download = function(app) {
      if (app.disabled) {
        return;
      }
      app.downloading = true;
      api.download(app, function(data) {
        if (data === 'err') {
          app.downloading = false;
          global.addAlert('danger', 'Error downloading app');
          return;
        }
        if (data.status === 'SUCCESS') {
          if (data.message.success.length === 0) {
            app.downloading = false;
            global.addAlert('warning', app.docid + ' can\'t be downloaded');
            return;
          }
        }
        app.downloading = false;
        app.disabled = true;
      });
    };
  }
});

app.component('loginView', {
  templateUrl: '/views/login.html',
  controller: function LoginController($location, api, global) {
    var ctrl = this;
    ctrl.current = 0;
    ctrl.max = -1;
    ctrl.formattedPercent = 0;
    ctrl.securityCheck = false;
    var polling = function() {
      api.getApps(function(response) {
        if (response === 'err') {
          ctrl.loggingIn = false;
          return;
        }
        if (response.status === 'UNAUTHORIZED') {
          return;
        }
        if (response.status === 'PENDING') {
          ctrl.loggingIn = true;
          if (response.total !== 0) {
            ctrl.max = response.total;
            ctrl.current = response.current;
            ctrl.formattedPercent = (ctrl.current / ctrl.max)*100;
            ctrl.formattedPercent = ctrl.formattedPercent.toFixed(1);
          }
        }
        if (response.status === 'SUCCESS') {
          global.auth.login();
          $location.path('/');
          ctrl.loggingIn = false;
          clearInterval(interval);
        }
      });
    };
    ctrl.loggingIn = false;
    ctrl.badUsername = false;
    ctrl.badPassword = false;

    polling();
    var interval = setInterval(polling, 3000);


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
          ctrl.securityCheck = data.securityCheck;
          return;
        }
      });
    };
  }
});
