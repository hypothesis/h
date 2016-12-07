'use strict';

// Header script which is included inline at the top of every page on the site.
//
// This should be a small script which does things like setting up flags to
// indicate that scripting is active, send analytics events etc.

const EnvironmentFlags = require('./base/environment-flags');

window.envFlags = new EnvironmentFlags(document.documentElement);
window.envFlags.init();
