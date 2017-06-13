const app = {};

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
    fetch('/gplay/getapks', {
      method: 'GET',
      headers: appHeaders
    }).then(response => {
      return response.text();
    }).then(text => {
      /*
       * Returned data is an object containing
       * objects, so we need to iterate through keys
       */
      console.log(text);
      let data = JSON.parse(text);
      
    });
  },
  events: {
  }
});

app.appView = new app.AppView();
