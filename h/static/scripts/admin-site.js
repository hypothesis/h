import 'bootstrap';

import { init as initSentry } from './base/sentry';
import { settings } from './base/settings';
import { upgradeElements } from './base/upgrade-elements';
import { sharedControllers } from './controllers';
import { AdminUsersController } from './controllers/admin-users-controller';

const appSettings = settings(document);
if (appSettings.sentry) {
  initSentry(appSettings.sentry);
}

const controllers = Object.assign(
  {},
  {
    '.js-users-delete-form': AdminUsersController,
  },
  sharedControllers,
);
upgradeElements(document.body, controllers);
window.envFlags.ready();
