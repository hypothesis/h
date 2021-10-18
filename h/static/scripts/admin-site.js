// configure error reporting
import { settings } from './base/settings';

const appSettings = settings(document);
if (appSettings.raven) {
  require('./base/raven').init(appSettings.raven);
}

window.$ = window.jQuery = require('jquery');
import 'bootstrap';

import { upgradeElements } from './base/upgrade-elements';
import * as sharedControllers from './controllers';

// Additional controllers for admin site.

import { AdminUsersController } from './controllers/admin-users-controller';

const controllers = Object.assign(
  {},
  {
    '.js-users-delete-form': AdminUsersController,
  },
  sharedControllers
);
upgradeElements(document.body, controllers);
window.envFlags.ready();
