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
  app.apkList.on('remove', apk => {

    // delete app on server
    fetch('/gplay/delete', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          'delete': apk.get('docId')
        })
      }).then(response => {
        return response.text();
      }).then(text => {
        if (text === 'OK') {
          console.log('I\'m in OK');
          let notification = '<div class="alert message alert-success alert-dismissible fade in" role="alert">' +
            '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
            '<span aria-hidden="true">&times;</span></button>' +
            apk.get('docId') + ' succesfuly removed!</div>';
          $('body').append(notification);
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

    initialize: function () {
      this.updateAvailable = false;
    },

    render: function(){
      this.$el.html(this.template(this.model.toJSON()));

      // set update button as disables
      this.$('#apk-item-update').attr('class', 'btn btn-default');
      //this.$('#apk-item-update').removeAttr('href');
      this.$('#apk-item-update').prop('disabled', true);
      this.$('#apk-item-update').css('cursor', 'default');

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
      //render loading bar
      this.template = _.template($('#loading-template').html());
      this.render();

      let view = this;
      if (this.updateAvailable) {
        console.log('Updating ' + view.model.get('docId'));
        fetch('/gplay/download', {
          method: 'POST',
          headers: headers,
          body: JSON.stringify({
            download: [view.model.get('docId')]
          })
        }).then(response => {
          return response.text();
        }).then(text => {
          let result = JSON.parse(text);
          if (result.success.length > 0) {
            view.model.set('version', result.success[0].version);
          }

          // restore view
          view.template = _.template($('#apk-template').html());
          view.render();
        });
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
