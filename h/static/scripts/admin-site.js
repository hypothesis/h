'use strict';

// configure error reporting
var settings = require('./settings')(document);
if (settings.raven) {
  require('./raven').init(settings.raven);
}

window.$ = window.jQuery = require('jquery');
require('bootstrap');

var AdminUsersController = require('./controllers/admin-users-controller');
var upgradeElements = require('./controllers/upgrade-elements');

var controllers = {
  '.js-users-delete-form': AdminUsersController,
};

upgradeElements(document.body, controllers);

