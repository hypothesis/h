'use strict';

// configure error reporting
const settings = require('./base/settings')(document);
if (settings.raven) {
  require('./base/raven').init(settings.raven);
}

window.$ = window.jQuery = require('jquery');
require('bootstrap');

const AdminUsersController = require('./controllers/admin-users-controller');
const upgradeElements = require('./base/upgrade-elements');

const controllers = {
  '.js-users-delete-form': AdminUsersController,
};

upgradeElements(document.body, controllers);

