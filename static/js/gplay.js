$(function(){

  const app = {};

  const headers = new Headers();
  headers.append('Content-Type', 'application/json');

  $.material.init();

  /*
   * MODELS
   */

  app.Apk = Backbone.Model.extend({
    defaults: {
      title: '',
      developer: '',
      size: '',
      numDownloads: '',
      uploadDate: '',
      docId: '',
      version: -1,
      stars: ''
    }
  });

  /*
   * COLLECTIONS
   */

  app.ApkList = Backbone.Collection.extend({
    model: app.Apk,
    url: '/gplay/getapps',
    initialize: function() {}
  });
  app.apkList = new app.ApkList();
  app.apkList.on('remove', app => {
    // delete app on server
    fetch('/gplay/delete', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          'delete': app.get('docId')
        })
      }).then(response => {
        return response.text();
      }).then(text => {
        if (text === 'OK')
          console.log('deleted ' + app.get('docId'));
      }).catch(error => {
        console.log(error);
      });

    //delete app view
  });

  /*
   * VIEWS
   */

  app.ApkView = Backbone.View.extend({
    template: _.template($('#apk-template').html()),
    render: function(){
      this.$el.html(this.template(this.model.toJSON()));

      // set the button to send delete request
      this.$('#apk-item-delete').click(() => {
        app.apkList.remove(this.model);
        this.remove();
      });
      this.$('#apk-item-update').prop('disabled', true);
      return this;
    }
  });

  app.appViewManager = {
    currentView: null,
    showView: view => {
      if (this.currentView != null) {
        console.log('currentView is initializated');
      }
      if (this.currentView != null &&
          this.currentView.cid !== view.cid)
      {
        this.currentView.remove();
      }
      this.currentView = view;
      return this.currentView.render();
    }
  };

  app.AppView = Backbone.View.extend({
    el: '#container',
    initialize: function () {
      this.getLocalApkList();
      $('#search-page-link').click(() => {
        Backbone.history.navigate('search', {trigger: true});
      });
    },
    getLocalApkList: function () {
      app.apkList.fetch({
        success: this.onLoad
      });
    },
    onLoad: function(apks, response) {
      apks.models.forEach(apk => {
        let view = new app.ApkView({
          model: apk
        });
        $('#container').append(view.render().el);
      });
    },
    events: {}
  });

  app.SearchView = Backbone.View.extend({
    el: '#container',
    template: _.template($('#search-template').html()),
    initialize: function () {
      $('#app-page-link').click(() => {
        Backbone.history.navigate('', {trigger: true});
      });
    },
    render: () => {
      this.$el.html(this.template());
      return this;
    }
  });

  /*
   * ROUTER
   */

  app.Router = Backbone.Router.extend({
    routes: {
        '' : 'index',
        'search' : 'search'
    },
    index: () => {
      let indexView = new app.AppView();
      app.appViewManager.showView(indexView);
    },
    search: () => {
      let searchView = new app.SearchView();
      app.appViewManager.showView(searchView);
    }
  });

  app.appRouter = new app.Router();

  Backbone.history.start();

}); // end jquery onload function
