import { init as initSentry } from './base/sentry';
import { settings } from './base/settings';
import { upgradeElements } from './base/upgrade-elements';
import { sharedControllers } from './controllers';
import { AuthorizeFormController } from './controllers/authorize-form-controller';
import { SearchBarController } from './controllers/search-bar-controller';
import { SearchBucketController } from './controllers/search-bucket-controller';
import { ShareWidgetController } from './controllers/share-widget-controller';

const appSettings = settings(document);
if (appSettings.sentry) {
  initSentry(appSettings.sentry);
}

const controllers = Object.assign(
  {
    '.js-authorize-form': AuthorizeFormController,
    '.js-search-bar': SearchBarController,
    '.js-search-bucket': SearchBucketController,
    '.js-share-widget': ShareWidgetController,
  },
  sharedControllers,
);

if (window.envFlags && window.envFlags.get('js-capable')) {
  upgradeElements(document.body, controllers);
  window.envFlags.ready();
} else {
  // Environment flags not initialized. The header script may have been missed
  // in the page or may have failed to load.
  console.warn('EnvironmentFlags not initialized. Skipping element upgrades');
}
