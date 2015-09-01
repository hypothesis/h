(function(h) {
  'use strict';

  /**
   * Validate and normalize the given settings data.
   *
   * @param {Object} settings The settings from the settings.json file.
   */
  function normalizeSettings(settings) {

    // Make sure that serviceUrl does not end with a /.
    if (settings.serviceUrl.charAt(settings.serviceUrl.length - 1) === '/') {
      settings.serviceUrl = settings.serviceUrl.slice(0, -1);
    }

  }

  function getSettings() {
    return new Promise(function(resolve, reject) {
      var request = new XMLHttpRequest();
      request.onload = function() {
        var settings = JSON.parse(this.responseText);
        normalizeSettings(settings);
        resolve(settings);
      };
      request.open('GET', '/settings.json');
      request.send(null);
    });
  }

  /**
   * A Promise whose value is the contents of the settings.json file.
   * @example
   * h.settings.then(function(settings) {
   *   // Do something with the settings object.
   * });
   */
  h.settings = getSettings();

})(window.h || (window.h = {}));
