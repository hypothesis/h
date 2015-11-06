'use strict';

/**
 * Validate and normalize the given settings data.
 *
 * @param {Object} settings The settings from the settings.json file.
 */
function normalizeSettings(settings) {
  // Make sure that apiUrl does not end with a /.
  if (settings.apiUrl.charAt(settings.apiUrl.length - 1) === '/') {
    settings.apiUrl = settings.apiUrl.slice(0, -1);
  }
  return settings;
}

/**
 * Returns the configuration object for the Chrome extension
 */
module.exports = normalizeSettings(window.EXTENSION_CONFIG);
