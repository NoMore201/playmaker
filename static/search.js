$(function () {
  const app = {};

  const headers = new Headers();
  headers.append('Content-Type', 'application/json');

  $.material.init();

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

  app.ApkList = Backbone.Collection.extend({
    model: app.Apk
  });

  app.apkList = new app.ApkList();

  app.ItemView = Backbone.View.extend({

    tagName: 'tr',
    
    template: _.template($('#table-item-template').html()),

    render: function () {
      this.$el.html(this.template(this.model.toJSON()));

      return this;
    },

    events: {
      'click .dl-button': 'download'
    },

    download: function () {
      console.log('Downloading ' + this.model.get('title'));
    }

  });

  app.TableView = Backbone.View.extend({

    tagName: 'table',

    className: 'table table-hover',

    template: _.template($('#table-template').html()),

    render: function(data){
      this.$el.html(this.template());

      this.tBody = this.$('#table-body');

      app.apkList.add(data);
      app.apkList.models.forEach(m => {
        let view = new app.ItemView({
          model: m
        });
        this.tBody.append(view.render().el);
      });
      return this;
    }

  });

  app.AppView = Backbone.View.extend({

    el: '#container',

    initialize: function () {
      this.tableBox = this.$('#table-box');
      this.searchInput = this.$('#search-input');
    },

    events: {
      'keypress #search-input': 'searchApps'
    },

    searchApps: function (e) {
      if (e.keyCode !== 13) {
        return;
      }

      let text = this.searchInput.val();
      if (text.length === 0) {
        return;
      }

      //TODO filter text
      let url = '/gplay/search';
      url = url + '?search=' + text;
      url = url + '&numEntries=10';

      fetch(url, {
        method: 'GET',
        headers: headers
      }).then( response => {
        return response.text();
      }).then( text => {
        let data = JSON.parse(text);
        let table = new app.TableView();
        this.tableBox.append(table.render(data).el);
      })
    }

  });

  app.appView = new app.AppView();

});
