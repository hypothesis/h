var raven = require('../../../static/scripts/raven');
if (window.EXTENSION_CONFIG.raven) {
  raven.init(window.EXTENSION_CONFIG.raven);
}

require('./polyfills');
require('./hypothesis-chrome-extension');
require('./install');
