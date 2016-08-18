'use strict';

// Configure error reporting
var settings = require('./base/settings')(document);
if (settings.raven) {
  require('./base/raven').init(settings.raven);
}

require('./polyfills');

var CreateGroupFormController = require('./controllers/create-group-form-controller');
var DropdownMenuController = require('./controllers/dropdown-menu-controller');
var FormSelectOnFocusController = require('./controllers/form-select-onfocus-controller');
var SearchBucketController = require('./controllers/search-bucket-controller');
var upgradeElements = require('./base/upgrade-elements');

var controllers = {
  '.js-create-group-form': CreateGroupFormController,
  '.js-dropdown-menu': DropdownMenuController,
  '.js-select-onfocus': FormSelectOnFocusController,
  '.js-search-bucket': SearchBucketController,
};

upgradeElements(document.body, controllers);

if (window.envFlags) {
  window.envFlags.ready();
}
