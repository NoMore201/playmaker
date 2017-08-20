$(function () {
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


  // Resources
  const loadingSpinner = '<i class="fa fa-refresh fa-spin fa-2x fa-fw"></i>';
  const downloadIcon = '<i class="fa fa-download fa-2x" aria-hidden="true"></i>';

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
      this.$('.dl-button').html(loadingSpinner);
      fetch('/api/download', {
        method: 'POST',
        headers: headers,
        credentials: 'same-origin',
        body: JSON.stringify({
          download: [this.model.get('docId')]
        })
      }).then(response => {
        return response.text();
      }).then(text => {
        let data = JSON.parse(text);
        if (data.failed.length === 0) {
          this.$('.dl-button').html(downloadIcon);
          this.$('.dl-button').css('cursor', 'default');
          this.$('.dl-button').css('pointer-events', 'none');
          this.$('.dl-button').css('color', '#BABABA');
        } else {
          genErrorAlertHtml('Error while downloading ' + this.model.get('docId'));
          this.$('.dl-button').html(downloadIcon);
        }
      }).catch(error => {
        genErrorAlertHtml('Error while downloading ' + this.model.get('docId'));
        this.$('.dl-button').html(downloadIcon);
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

      if (data === undefined) {
        return;
      }
      if (app.apkList.models.length > 0) {
        app.apkList.reset()
      }
      app.apkList.add(data);
      app.apkList.models.forEach(m => {
        let view = new app.ItemView({
          model: m
        });
        this.tBody.append(view.render().el);
        let title = m.get('title');
        if (title.length > 35) {
          title = title.substring(0, 32) + '..';
        }
        let popover = view.$('[data-toggle="popover"]');
        popover.isVisible = false;
        popover.attr('title',
          '<strong>' + title + '</strong>');
        popover.attr('data-content',
          '<strong>Id:</strong> ' + m.get('docId') + '<br>' +
          '<strong>Dev:</strong> ' + m.get('developer') + '<br>' +
          '<strong>Size:</strong> ' + m.get('size') + '<br>' +
          '<strong>Stars:</strong> ' + m.get('stars') + '<br>');
        popover.popover();
      });
      return this;
    }

  });

  app.AppView = Backbone.View.extend({

    el: '#container',

    initialize: function () {
      this.tableBox = this.$('#table-box');
      this.searchInput = this.$('#search-input');
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
      let t =  _.template($('#loading-template').html())
      this.tableBox.html(t());

      let text = this.searchInput.val();
      if (text.length === 0) {
        return;
      }

      //TODO filter text
      let url = '/api/search';
      url = url + '?search=' + text;

      fetch(url, {
        method: 'GET',
        credentials: 'same-origin',
        headers: headers
      }).then( response => {
        return response.text();
      }).then( text => {
        let data = JSON.parse(text);
        let table = new app.TableView();
        this.tableBox.html(table.render(data).el);
      }).catch(error => {
        this.tableBox.html('');
        genErrorAlertHtml('Error while searching');
      });
    }

  });

  app.appView = new app.AppView();

});
