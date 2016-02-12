'use strict';

require('core-js/fn/object/assign');

/**
 * Return application configuration information from the host page.
 *
 * Exposes shared application settings, read from script tags with the
 * class 'js-hypothesis-settings' which contain JSON content.
 *
 * If there are multiple such tags, the configuration from each is merged.
 *
 * @param {Document|Element} document - The root element to search for
 *                                      <script> settings tags.
 */
function settings(document) {
  var settingsElements =
    document.querySelectorAll('script.js-hypothesis-settings');

  var config = {};
  for (var i=0; i < settingsElements.length; i++) {
    Object.assign(config, JSON.parse(settingsElements[i].textContent));
  }
  return config;
}

module.exports = settings;
