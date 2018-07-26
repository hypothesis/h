'use strict';

// Configure error reporting
const settings = require('./base/settings')(document);
if (settings.raven) {
  const raven = require('./base/raven');
  raven.init(settings.raven);
}

require('./polyfills');

const sharedControllers = require('./controllers');
const upgradeElements = require('./base/upgrade-elements');

// Additional controllers for user-facing site.
const AuthorizeFormController = require('./controllers/authorize-form-controller');
const CreateGroupFormController = require('./controllers/create-group-form-controller');
const SearchBarController = require('./controllers/search-bar-controller');
const SearchBucketController = require('./controllers/search-bucket-controller');
const ShareWidgetController = require('./controllers/share-widget-controller');
const SignupFormController = require('./controllers/signup-form-controller');

const controllers = Object.assign({
  '.js-authorize-form': AuthorizeFormController,
  '.js-create-group-form': CreateGroupFormController,
  '.js-search-bar': SearchBarController,
  '.js-search-bucket': SearchBucketController,
  '.js-share-widget': ShareWidgetController,
  '.js-signup-form': SignupFormController,
}, sharedControllers);

if (window.envFlags && window.envFlags.get('js-capable')) {
  upgradeElements(document.body, controllers);
  window.envFlags.ready();
} else {
  // Environment flags not initialized. The header script may have been missed
  // in the page or may have failed to load.
  console.warn('EnvironmentFlags not initialized. Skipping element upgrades');
}
