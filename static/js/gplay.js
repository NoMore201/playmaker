$(function(){

  const app = {};

  $.material.init();

  const appHeaders = new Headers();
  appHeaders.append("Content-Type", "application.json");

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

  app.ApkView = Backbone.View.extend({
    template: _.template($('#apk-template').html()),
    render: function(){
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    }
  });

  app.LoadAlertView = Backbone.View.extend({
    tagName: 'div',
    id: 'loading-alert',
    className: 'alert alert-dismissible alert-info',
    template: '<button type="button" class="close" data-dismiss="alert">×</button>' +
              '<strong><%- message %></strong>',
    initialize: function() {
      this.template = _.template(this.template);
    },
    render: function() {
      let output = this.template({message: 'Loading apks..'});
      this.$el.html(output);
      return this;
    }
  });
  app.loadAlertView = new app.LoadAlertView();

  app.AppView = Backbone.View.extend({
    el: '#container',
    initialize: function () {
      $('body').append(app.loadAlertView.render().el);
      this.getLocalApkList();
    },
    getLocalApkList: function () {
      app.apkList.fetch({
        success: this.onLoad
      });
    },
    onLoad: function(apks, response) {
      let load = this.loadAlertView;
      apks.models.forEach(apk => {
        let view = new app.ApkView({
          model: apk
        });
        $('#container').append(view.render().el);
      });
      app.loadAlertView.remove();
    },
    events: {}
  });

  app.appView = new app.AppView();

}); // end jquery onload function
