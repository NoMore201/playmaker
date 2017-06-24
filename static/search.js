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
      'click .dl-button': 'download',
      'click .info-button': 'showInfo'
    },

    download: function () {
      $('#loading-modal').show();
      fetch('/gplay/download', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          download: [this.model.get('docId')]
        })
      }).then(response => {
        return response.text();
      }).then(text => {
        let data = JSON.parse(text);
        if (data.failed.length === 0) {
          this.$('.dl-button').css('cursor', 'default');
          this.$('.dl-button').css('pointer-events', 'none');
          this.$('.dl-button').css('color', '#BABABA');
          //TODO: display error msg
        }
        $('#loading-modal').hide();
      });
    },

    showInfo: function () {
      let modal = $('#info-modal');
      $('#info-modal-body').html(
          '<span><strong>Id:</strong> ' + this.model.get('docId') + '</span><br>' +
          '<span><strong>Dev:</strong> ' + this.model.get('developer') + '</span><br>' +
          '<span><strong>Version:</strong> ' + this.model.get('version') + '</span><br>' +
          '<span><strong>Uploaded:</strong> ' + this.model.get('uploadDate') + '</span><br>'
      );
      modal.show();
      modal.click( function () {
        modal.hide();
      });
    }

  });

  app.TableView = Backbone.View.extend({

    id: 'search-table',

    tagName: 'table',

    className: 'table table-hover',

    template: _.template($('#table-template').html()),

    render: function(data){
      this.$el.html(this.template());

      this.tBody = this.$('#table-body');

      if (app.apkList.models.length !== 0) {
        app.apkList.reset()
      }
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
      this.spinner = $('#loading-spinner');
      this.spinner.hide();
      this.modal = $('#loading-modal');
      this.modal.hide();
      this.infoModal = $('#info-modal');
      this.infoModal.hide();
    },

    events: {
      'keypress #search-input': 'searchApps'
    },

    searchApps: function (e) {
      if (e.keyCode !== 13) {
        return;
      }

      // reset the table view
      this.tableBox.html('');
      this.spinner.show();

      let text = this.searchInput.val();
      if (text.length === 0) {
        return;
      }

      //TODO filter text
      let url = '/gplay/search';
      url = url + '?search=' + text;
      url = url + '&numEntries=15';

      fetch(url, {
        method: 'GET',
        headers: headers
      }).then( response => {
        return response.text();
      }).then( text => {
        let data = JSON.parse(text);
        let table = new app.TableView();
        this.spinner.hide();
        this.tableBox.html(table.render(data).el);
      })
    }

  });

  app.appView = new app.AppView();

});
