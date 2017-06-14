$(function(){

  const app = {};

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

  app.ApkView = Backbone.View.extend({
    template: _.template($('#apk-template').html()),
    render: function(){
      this.$el.html(this.template(this.model.toJSON()));
      return this;
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
        $('#container').append(view.render().el);
      });
    },
    events: {}
  });

  app.appView = new app.AppView();

}); // end jquery onload function
