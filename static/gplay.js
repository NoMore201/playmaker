$(function(){

  const app = {};

  const headers = new Headers();
  headers.append('Content-Type', 'application/json');

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

    url: '/gplay/getapps'

  });

  // initialize view list, used to enable
  // update on apks
  app.apkViews = [];

  // instance of the collection
  app.apkList = new app.ApkList();

  // after removing an element from collection
  // fire a delete request to the server
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
        if (text === 'OK') {
        }
      }).catch(error => {
        console.log(error);
      });

  });



  /*
   * VIEWS
   */

  app.ApkView = Backbone.View.extend({

    template: _.template($('#apk-template').html()),

    render: function(){
      this.$el.html(this.template(this.model.toJSON()));

      // set update button as disables
      this.$('#apk-item-update').attr('class', 'btn btn-default');
      //this.$('#apk-item-update').removeAttr('href');
      this.$('#apk-item-update').prop('disabled', true);
      this.$('#apk-item-update').css('cursor', 'default');

      this.updateAvailable = false;
      return this;
    },

    events: {
      'click #apk-item-delete': 'onClickDelete',
      'click #apk-item-update': 'onClickUpdate'
    },

    onClickDelete: function() {
      let appName = this.model.get('docId');
      app.apkList.remove(this.model);
      let index = app.apkViews.findIndex(function (view) {
        return view.model.get('docId') === appName;
      });
      app.apkViews.splice(index, 1);
      this.remove();
    },

    onClickUpdate: function() {
      if (this.updateAvailable) {
        console.log('Updating ' + this.model.get('docId'));
        // TODO: update app and then reset boolean
      }
    },

    enableUpdateBtn: function() {
      this.$('#apk-item-update').prop('disabled', false);
      this.$('#apk-item-update').css('cursor', 'pointer');
      this.$('#apk-item-update').attr('class', 'btn btn-raised btn-primary');
      this.updateAvailable = true;
    }

  });

  app.AppView = Backbone.View.extend({

    el: '#container',

    initialize: function () {
      this.updateAllBtn = $('#update-all');

      // fetch apks from server
      app.apkList.fetch({
        success: function(apks, response) {
          apks.models.forEach(apk => {
            let view = new app.ApkView({
              model: apk
            });
            this.$('#container').append(view.render().el);
            app.apkViews.push(view);
          });
        }
      });
    },

    events: {
      'click #update-all': 'updateAll'
    },

    updateAll: function(e) {
      fetch('/gplay/check', {
        method: 'POST',
        headers: headers
      }).then(function (response) {
        return response.text();
      }).then(function (text) {
        let result = JSON.parse(text);
        console.log(result);
        let viewSet = app.apkViews;

        if (result.length > 0) {
          result.forEach( function (app) {
            let relatedView = viewSet.find( function(view) {
              return view.model.get('docId') === app;
            });
            if (relatedView !== undefined) {
              relatedView.enableUpdateBtn();
            }
          });
        }
      }).catch(error => {
        console.log(error);
      });
    }

  });

  // initialize main Apps view
  app.appView = new app.AppView();

}); // end jquery onload function
