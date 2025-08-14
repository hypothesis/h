// Header script which is included inline at the top of every page on the site.
//
// This should be a small script which does things like sending analytics
// events.

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
