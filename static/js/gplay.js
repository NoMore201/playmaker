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
    url: '/gplay/getapps'
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

      // set update button as disables
      this.$('#apk-item-update').prop('disabled', true);
      return this;
    },
    events: {
      'click #apk-item-delete': 'onClickDelete'
    },
    onClickDelete: function() {
      app.apkList.remove(this.model);
      this.remove();
    }
  });

  app.AppView = Backbone.View.extend({
    el: '#container',
    initialize: function () {
      this.getLocalApkList();
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
        this.$el.append(view.render().el);
      });
    }
  });

  // initialize main Apps view
  app.appView = new app.AppView();

}); // end jquery onload function
