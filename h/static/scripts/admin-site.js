'use strict';

// configure error reporting
const settings = require('./base/settings')(document);
if (settings.raven) {
  require('./base/raven').init(settings.raven);
}

window.$ = window.jQuery = require('jquery');
require('bootstrap');

const AdminGroupsController = require('./controllers/admin-groups-controller');
const AdminUsersController = require('./controllers/admin-users-controller');
const ConfirmSubmitController = require('./controllers/confirm-submit-controller');
const FormController = require('./controllers/form-controller');
const TooltipController = require('./controllers/tooltip-controller');
const upgradeElements = require('./base/upgrade-elements');

const controllers = {
  '.js-confirm-submit': ConfirmSubmitController,
  '.js-form': FormController,
  '.js-tooltip': TooltipController,
  '.js-users-delete-form': AdminUsersController,
  '.js-groups-delete-form': AdminGroupsController,
};

upgradeElements(document.body, controllers);
window.envFlags.ready();
