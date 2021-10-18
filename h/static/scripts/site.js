import { settings } from './base/settings';

// Configure error reporting
const appSettings = settings(document);
if (appSettings.raven) {
  const raven = require('./base/raven');
  raven.init(appSettings.raven);
}

import './polyfills';

import { upgradeElements } from './base/upgrade-elements';
import sharedControllers from './controllers';

// Additional controllers for user-facing site.
import { AuthorizeFormController } from './controllers/authorize-form-controller';
import { CreateGroupFormController } from './controllers/create-group-form-controller';
import { SearchBarController } from './controllers/search-bar-controller';
import { SearchBucketController } from './controllers/search-bucket-controller';
import { ShareWidgetController } from './controllers/share-widget-controller';

const controllers = Object.assign(
  {
    '.js-authorize-form': AuthorizeFormController,
    '.js-create-group-form': CreateGroupFormController,
    '.js-search-bar': SearchBarController,
    '.js-search-bucket': SearchBucketController,
    '.js-share-widget': ShareWidgetController,
  },
  sharedControllers
);

if (window.envFlags && window.envFlags.get('js-capable')) {
  upgradeElements(document.body, controllers);
  window.envFlags.ready();
} else {
  // Environment flags not initialized. The header script may have been missed
  // in the page or may have failed to load.
  console.warn('EnvironmentFlags not initialized. Skipping element upgrades');
}
