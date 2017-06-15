$(function () {
  const app = {};

  const headers = new Headers();
  headers.append('Content-Type', 'application/json');

  $.material.init();
 
  app.SearchView = Backbone.View.extend({
    template: _.template($('#search-template').html()),
    render: function() {
      this.$el.html(this.template());
      return this;
    }
  });

  app.AppView = Backbone.View.extend({
    el: '#container',
    initialize: function () {
      this.render();
      this.tableBox = this.$('#table-box');
      let searchView = new app.SearchView();
      this.$el.append(searchView.render().el);
    }
  });



  app.appView = new app.AppView();

});
