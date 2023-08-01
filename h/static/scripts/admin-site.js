import 'bootstrap';

import { init as initRaven } from './base/raven';
import { settings } from './base/settings';
import { upgradeElements } from './base/upgrade-elements';
import { sharedControllers } from './controllers';
import { AdminUsersController } from './controllers/admin-users-controller';

const appSettings = settings(document);
if (appSettings.raven) {
  initRaven(appSettings.raven);
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
