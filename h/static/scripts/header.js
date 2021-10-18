// Header script which is included inline at the top of every page on the site.
//
// This should be a small script which does things like setting up flags to
// indicate that scripting is active, send analytics events etc.

import { EnvironmentFlags } from './base/environment-flags';

window.envFlags = new EnvironmentFlags(document.documentElement);
window.envFlags.init();

// Set up the Google Analytics command queue if we have a tracking ID.
const gaTrackingId = document.querySelector(
  'meta[name="google-analytics-tracking-id"]'
);
if (gaTrackingId) {
  /* eslint-disable */
  window.ga =
    window.ga ||
    function () {
      (ga.q = ga.q || []).push(arguments);
    };
  ga.l = +new Date();
  ga('create', gaTrackingId.content, 'auto');
  ga('set', 'anonymizeIp', true);
  ga('send', 'pageview');
  /* eslint-enable */
}
