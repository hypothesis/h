'use strict';

/**
 * @ngdoc factory
 * @name  settings
 *
 * @description
 * The 'settings' factory exposes shared application settings, read from a
 * script tag with type "application/json" and id "hypothesis-settings" in the
 * app page.
 */
// @ngInject
function settings($document) {
  var settingsElement = $document[0].querySelector(
    'script[type="application/json"]#hypothesis-settings');

  if (settingsElement) {
    return JSON.parse(settingsElement.textContent);
  }

  return {};
}

module.exports = settings;
