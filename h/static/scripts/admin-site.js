'use strict';

// configure error reporting
const settings = require('./base/settings')(document);
if (settings.raven) {
  require('./base/raven').init(settings.raven);
}

const sharedControllers = require('./controllers');
const upgradeElements = require('./base/upgrade-elements');

// Additional controllers for admin site.
const AdminUsersController = require('./controllers/admin-users-controller');
const AdminMenuToggleController = require('./controllers/admin-menu-toggle-controller');
const AlertCloseButtonController = require('./controllers/alert-close-button-controller');

const controllers = Object.assign({}, {
  '.js-users-delete-form': AdminUsersController,
  '.js-admin-navbar__menu-toggle': AdminMenuToggleController,
  '.js-alert-close-button': AlertCloseButtonController,
}, sharedControllers);
upgradeElements(document.body, controllers);
window.envFlags.ready();
