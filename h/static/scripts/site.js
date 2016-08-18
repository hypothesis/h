'use strict';

// Configure error reporting
var settings = require('./base/settings')(document);
if (settings.raven) {
  require('./base/raven').init(settings.raven);
}

require('./polyfills');

var CharacterLimitController = require('./controllers/character-limit-controller');
var CreateGroupFormController = require('./controllers/create-group-form-controller');
var DropdownMenuController = require('./controllers/dropdown-menu-controller');
var FormSelectOnFocusController = require('./controllers/form-select-onfocus-controller');
var FormController = require('./controllers/form-controller');
var SearchBucketController = require('./controllers/search-bucket-controller');
var TooltipController = require('./controllers/tooltip-controller');
var upgradeElements = require('./base/upgrade-elements');

var controllers = {
  '.js-character-limit': CharacterLimitController,
  '.js-create-group-form': CreateGroupFormController,
  '.js-dropdown-menu': DropdownMenuController,
  '.js-form': FormController,
  '.js-select-onfocus': FormSelectOnFocusController,
  '.js-search-bucket': SearchBucketController,
  '.js-tooltip': TooltipController,
};

var doUpgrade = !window.envFlags || window.envFlags.get('js-capable');

if (doUpgrade) {
  upgradeElements(document.body, controllers);
}

if (window.envFlags) {
  window.envFlags.ready();
}
