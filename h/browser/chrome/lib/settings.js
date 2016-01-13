/**
 * A wrapper for the settings.json file that ships with the Chrome extension.
 * @module
 */
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

function getSettings() {
  return fetch('/settings.json').then(function (res) {
    return res.json();
  }).then(function (settings) {
    return normalizeSettings(settings);
  });
}

/**
 * A Promise whose value is the contents of the settings.json file.
 *
 * @example
 * settings.then(function(settings) {
 *   // Do something with the settings object.
 * });
 */
module.exports = getSettings();
