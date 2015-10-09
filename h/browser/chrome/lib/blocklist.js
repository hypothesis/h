/**
 * A wrapper for the app's /blocklist HTTP endpoint.
 * @module
 */
'use strict';

var settings = require('./settings');

/**
  * Return a Promise that resolves to whether the URI is blocked and how many
  * annotations it has.
  *
  * @function
  * @param {String} uri The URI to be checked
  * @returns {Promise} A Promise that resolves to an object with two
  *   properties, `total`: the number of annotations there are of this URI
  *   (number); and `blocked`: whether or not this URI is blocklisted
  *   (boolean). The Promise may also be rejected.
  */
function getBlocklist(uri) {
  return new Promise(function(resolve, reject) {
    var request = new XMLHttpRequest();
    request.onload = function() {
      var blocklist;
      var total;
      var blocked;
      var errorMsg;

      try {
        blocklist = JSON.parse(this.responseText);
        total = blocklist.total;
        blocked = blocklist.blocked;
      } catch (e) {
        errorMsg = 'Received invalid JSON from the /blocklist endpoint: ';
        errorMsg = errorMsg + this.responseText;
        console.error(errorMsg);
        reject(errorMsg);
        return;
      }

      if (typeof total !== 'number') {
        errorMsg = 'Received invalid total from the /blocklist endpoint: ';
        errorMsg = errorMsg + total;
        console.error(errorMsg);
        reject(errorMsg);
        return;
      }

      if (typeof blocked !== 'boolean') {
        errorMsg = 'Received invalid blocked from the /blocklist endpoint: ';
        errorMsg = errorMsg + total;
        console.error(errorMsg);
        reject(errorMsg);
        return;
      }

      resolve({total: total, blocked: blocked});
    };

    request.ontimeout = function() {
      reject('the blocklist HTTP request timed out');
    };

    settings.then(function(settings) {
      request.open('GET', settings.serviceUrl + '/blocklist?uri=' + uri);
      request.send(null);
    });
  });
}

module.exports = getBlocklist;
