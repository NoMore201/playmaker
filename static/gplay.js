$(function(){

  const app = {};

  const headers = new Headers();
  headers.append('Content-Type', 'application/json');

  /**
   * GENERIC FUNCTIONS
   */

  function genInfoAlertHtml(message) {
    let n = _.template($('#alert-info-tmp').html());
    n = n({ message: message });
    let view = $(n);
    $('body').append(view);
    setTimeout( function() {
      view.alert('close');
    }, 5000);
  }

  function genSuccessAlertHtml(message) {
    let n = _.template($('#alert-success-tmp').html());
    n = n({ message: message });
    let view = $(n);
    $('body').append(view);
    setTimeout( function() {
      view.alert('close');
    }, 5000);
  }

  function genErrorAlertHtml(message) {
    let n = _.template($('#alert-error-tmp').html());
    n = n({ message: message });
    let view = $(n);
    $('body').append(view);
    setTimeout( function() {
      view.alert('close');
    }, 5000);
  }

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
    model: app.Apk
  });

  // initialize view list, used to enable
  // update on apks
  app.apkViews = [];

  // instance of the collection
  app.apkList = new app.ApkList();


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

      // set update button as disabled
      this.$('#apk-item-update').attr('class', 'btn btn-default');
      this.$('#apk-item-update').prop('disabled', true);
      this.$('#apk-item-update').css('cursor', 'default');

      return this;
    },

    events: {
      'click #apk-item-delete': 'onClickDelete',
      'click #apk-item-update': 'onClickUpdate'
    },

    onClickDelete: function() {
      this.template = _.template($('#loading-template').html());
      this.render();
      let apk = this.model;
      let view = this;

      fetch('/api/delete', {
        method: 'POST',
        headers: headers,
        credentials: 'same-origin',
        body: JSON.stringify({
          'delete': apk.get('docId')
        })
      }).then(response => {
        if (response.status !== 200) {
          throw new Error();
        }
        return response.text();
      }).then(text => {
        if (text === 'OK') {
          genSuccessAlertHtml( 'Successfully deleted ' + apk.get('docId') );
          // remove view from html and from apkViews array
          // then remove apk from collection
          let index = app.apkViews.findIndex(function (v) {
            return v === view;
          });
          view.remove();
          app.apkViews.splice(index, 1);
          app.apkList.remove(apk);
        }
      }).catch(error => {
        genErrorAlertHtml( 'Error deleting ' + apk.get('docId'));

        // restore original view
        view.template = _.template($('#apk-template').html());
        view.render();
      });

    },

    onClickUpdate: function() {
      //render loading bar
      this.template = _.template($('#loading-template').html());
      this.render();

      let view = this;
      if (this.updateAvailable) {
        console.log('Updating ' + view.model.get('docId'));
        fetch('/api/download', {
          method: 'POST',
          headers: headers,
          credentials: 'same-origin',
          body: JSON.stringify({
            download: [view.model.get('docId')]
          })
        }).then(response => {
          return response.text();
        }).then(text => {
          let result = JSON.parse(text);
          if (result.success.length > 0) {
            view.model.set('version', result.success[0].version);
          } else {
            throw new Error();
          }

          // restore view
          view.template = _.template($('#apk-template').html());
          view.render();
        }).catch(error => {
          genErrorAlertHtml( 'Error updating ' + apk.get('docId') );

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

      fetch('/api/apks', {
        method: 'GET',
        credentials: 'same-origin',
        headers: headers
      }).then(response => {
        if (response.status !== 200) {
          throw new Error();
        }
        return response.text();
      }).then(text => {
        let data = JSON.parse(text);
        app.apkList.add(data);
        app.apkList.models.forEach( function(m) {
          let view = new app.ApkView({
            model: m
          });
          $('#container').append(view.render().el);
          app.apkViews.push(view);
        });
      }).catch(error => {
        genErrorAlertHtml('Cannot fetch applications :(');
      });
    },

    events: {
      'click #update-all': 'updateAll',
      'click #update-fdroid': 'updateFdroid'
    },

    updateAll: function(e) {
      if (app.apkViews.length === 0) {
        return;
      }

      fetch('/api/check', {
        method: 'POST',
        credentials: 'same-origin',
        headers: headers
      }).then(function (response) {
        if (response.status !== 200) {
          throw new Error();
        }
        return response.text();
      }).then(function (text) {
        let result = JSON.parse(text);
        let viewSet = app.apkViews;

        if (result.length > 0) {
          let n = genSuccessAlertHtml(result.length.toString() +
                    ' apps needs to be updated');
          $('body').append(n);
          result.forEach( function (app) {
            let relatedView = viewSet.find( function(view) {
              return view.model.get('docId') === app;
            });
            if (relatedView !== undefined) {
              relatedView.enableUpdateBtn();
            }
          });
        } else {
          let n = genInfoAlertHtml('No updates avaialble');
          $('body').append(n);
        }
      }).catch(error => {
        genErrorAlertHtml('Cannot check for updates :(');
      });
    },

    updateFdroid: function(e) {
      fetch('/api/fdroid', {
        method: 'POST',
        credentials: 'same-origin',
        headers: headers
      }).then(function (response) {
        if (response.status !== 200) {
          throw new Error();
        }
        return response.text();
      }).then(function (text) {
        if (text === 'OK') {
          $('#fdroid-modal').modal('hide');
          let n = genSuccessAlertHtml('Fdroid repo correctly updated');
          $('body').append(n);
        }
      }).catch(error => {
        $('#fdroid-modal').modal('hide');
        genErrorAlertHtml('Cannot update Fdroid repo :(');
      });
    }

  });

  // initialize main Apps view
  app.appView = new app.AppView();

}); // end jquery onload function
