// Header script which is included inline at the top of every page on the site.
//
// This should be a small script which does things like setting up flags to
// indicate that scripting is active, send analytics events etc.

import { EnvironmentFlags } from './base/environment-flags';

window.envFlags = new EnvironmentFlags(document.documentElement);
window.envFlags.init();

// See https://developers.google.com/analytics/devguides/migration/ua/analyticsjs-to-gtagjs
const gaMeasurementId = document.querySelector(
  'meta[name="google-analytics-measurement-id"]',
)?.content;
if (gaMeasurementId) {
  /* eslint-disable */
  window.dataLayer = window.dataLayer || [];
  function gtag() {
    dataLayer.push(arguments);
  }
  gtag('js', new Date());
  gtag('config', gaMeasurementId);
  /* eslint-enable */
}
