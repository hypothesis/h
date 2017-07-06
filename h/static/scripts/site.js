'use strict';

// Configure error reporting
const settings = require('./base/settings')(document);
if (settings.raven) {
  const raven = require('./base/raven');
  raven.init(settings.raven);
}

require('./polyfills');

const AuthorizeFormController = require('./controllers/authorize-form-controller');
const CharacterLimitController = require('./controllers/character-limit-controller');
const CopyButtonController = require('./controllers/copy-button-controller');
const ConfirmSubmitController = require('./controllers/confirm-submit-controller');
const CreateGroupFormController = require('./controllers/create-group-form-controller');
const DropdownMenuController = require('./controllers/dropdown-menu-controller');
const FormController = require('./controllers/form-controller');
const FormSelectOnFocusController = require('./controllers/form-select-onfocus-controller');
const InputAutofocusController = require('./controllers/input-autofocus-controller');
const SearchBarController = require('./controllers/search-bar-controller');
const SearchBucketController = require('./controllers/search-bucket-controller');
const ShareWidgetController = require('./controllers/share-widget-controller');
const SignupFormController = require('./controllers/signup-form-controller');
const TooltipController = require('./controllers/tooltip-controller');
const upgradeElements = require('./base/upgrade-elements');

const controllers = {
  '.js-authorize-form': AuthorizeFormController,
  '.js-character-limit': CharacterLimitController,
  '.js-copy-button': CopyButtonController,
  '.js-confirm-submit': ConfirmSubmitController,
  '.js-create-group-form': CreateGroupFormController,
  '.js-dropdown-menu': DropdownMenuController,
  '.js-form': FormController,
  '.js-input-autofocus': InputAutofocusController,
  '.js-select-onfocus': FormSelectOnFocusController,
  '.js-search-bar': SearchBarController,
  '.js-search-bucket': SearchBucketController,
  '.js-share-widget': ShareWidgetController,
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
