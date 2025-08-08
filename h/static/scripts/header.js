// Header script which is included inline at the top of every page on the site.
//
// This should be a small script which does things like setting up flags to
// indicate that scripting is active, send analytics events etc.
import { EnvironmentFlags } from './base/environment-flags';
import { notifyAuthStatus } from './util/login-status';

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

// Notify other tabs about whether the user is logged in.
//
// The main use for this is to streamline the flow where a user signs up from a
// login window opened by the client. If the user signs up via email, we require
// them to verify their address before they can log in. After they activate
// their account and log in, we want to notify the original auth popup window so
// it can continue and log in the user into the client.
notifyAuthStatus();
