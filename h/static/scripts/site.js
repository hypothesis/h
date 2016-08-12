'use strict';

// Configure error reporting
var settings = require('./settings')(document);
if (settings.raven) {
  require('./raven').init(settings.raven);
}

require('./polyfills');

var CreateGroupFormController = require('./create-group-form');
var DropdownMenuController = require('./dropdown-menu-controller');
var FormSelectOnFocusController = require('./form-select-onfocus-controller');
var upgradeElements = require('./upgrade-elements');

var controllers = {
  '.js-create-group-form': CreateGroupFormController,
  '.js-dropdown-menu': DropdownMenuController,
  '.js-select-onfocus': FormSelectOnFocusController,
};

upgradeElements(document.body, controllers);
