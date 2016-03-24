'use strict';

// configure error reporting
var settings = require('./settings')(document);
if (settings.raven) {
  require('./raven').init(settings.raven);
}

window.$ = window.jQuery = require('jquery');
require('bootstrap');

var page = require('page');

var AdminUsersController = require('./admin-users');

page('/admin/users', function() {
  new AdminUsersController(document.body, window);
});

document.addEventListener('DOMContentLoaded', function () {
  page.start();
});
