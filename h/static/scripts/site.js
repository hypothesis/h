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
var FormController = require('./controllers/form-controller');
var FormSelectOnFocusController = require('./controllers/form-select-onfocus-controller');
var SearchBarController = require('./controllers/search-bar-controller');
var SearchBucketController = require('./controllers/search-bucket-controller');
var SignupFormController = require('./controllers/signup-form-controller');
var TooltipController = require('./controllers/tooltip-controller');
var upgradeElements = require('./base/upgrade-elements');

var controllers = {
  '.js-character-limit': CharacterLimitController,
  '.js-create-group-form': CreateGroupFormController,
  '.js-dropdown-menu': DropdownMenuController,
  '.js-form': FormController,
  '.js-select-onfocus': FormSelectOnFocusController,
  '.js-search-bar': SearchBarController,
  '.js-search-bucket': SearchBucketController,
  '.js-signup-form': SignupFormController,
  '.js-tooltip': TooltipController,
};

if (window.envFlags && window.envFlags.get('js-capable')) {
  upgradeElements(document.body, controllers);
  window.envFlags.ready();
} else {
  // Environment flags not initialized. The header script may have been missed
  // in the page or may have failed to load.
  console.warn('EnvironmentFlags not initialized. Skipping element upgrades');
}
