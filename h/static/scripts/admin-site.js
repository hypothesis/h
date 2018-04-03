'use strict';

// configure error reporting
const settings = require('./base/settings')(document);
if (settings.raven) {
  require('./base/raven').init(settings.raven);
}

window.$ = window.jQuery = require('jquery');
require('bootstrap');

const sharedControllers = require('./controllers');
const upgradeElements = require('./base/upgrade-elements');

// Additional controllers for admin site.
const AdminUsersController = require('./controllers/admin-users-controller');

const controllers = Object.assign({}, {
  '.js-users-delete-form': AdminUsersController,
}, sharedControllers);
upgradeElements(document.body, controllers);
window.envFlags.ready();

