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
var SearchBarController = require('./controllers/search-bar-controller');
var SearchBucketController = require('./controllers/search-bucket-controller');
var SignupFormController = require('./controllers/signup-form-controller');
var TooltipController = require('./controllers/tooltip-controller');
var upgradeElements = require('./base/upgrade-elements');

var controllers = {
  '.js-character-limit': CharacterLimitController,
  '.js-create-group-form': CreateGroupFormController,
  '.js-dropdown-menu': DropdownMenuController,
  '.js-select-onfocus': FormSelectOnFocusController,
  '.js-search-bar': SearchBarController,
  '.js-search-bucket': SearchBucketController,
  '.js-signup-form': SignupFormController,
  '.js-tooltip': TooltipController,
};

var doUpgrade = !window.envFlags || window.envFlags.get('js-capable');

if (doUpgrade) {
  upgradeElements(document.body, controllers);
}

if (window.envFlags) {
  window.envFlags.ready();
}
