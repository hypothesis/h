'use strict';

// Configure error reporting
var settings = require('./settings')(document);
if (settings.raven) {
  require('./raven').init(settings.raven);
}

require('./polyfills');

var CreateGroupFormController = require('./controllers/create-group-form-controller');
var DropdownMenuController = require('./controllers/dropdown-menu-controller');
var FormSelectOnFocusController = require('./controllers/form-select-onfocus-controller');
var upgradeElements = require('./controllers/upgrade-elements');

var controllers = {
  '.js-create-group-form': CreateGroupFormController,
  '.js-dropdown-menu': DropdownMenuController,
  '.js-select-onfocus': FormSelectOnFocusController,
};

upgradeElements(document.body, controllers);
