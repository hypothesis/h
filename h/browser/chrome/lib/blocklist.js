/**
 * A wrapper for the app's /blocklist HTTP endpoint.
 * @module
 */
'use strict';

var settings = require('./settings');
var blocklistPromise;

/**
  * Make an HTTP request to the /blocklist endpoint and return a Promise that
  * resolves to the value of the response.
  *
  * This is a helper function for getBlocklistIfUriHasChanged() below, see
  * that function's docstring for more details.
  *
  */
function getBlocklist(uri) {
  if (!uri) {
    return Promise.reject({reason: 'uri was undefined'});
  }

  var p = new Promise(function(resolve, reject) {
    var request = new XMLHttpRequest();
    request.timeout = 1000;

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
        reject({reason: errorMsg});
        return;
      }

      if (typeof total !== 'number') {
        errorMsg = 'Received invalid total from the /blocklist endpoint: ';
        errorMsg = errorMsg + total;
        console.error(errorMsg);
        reject({reason: errorMsg});
        return;
      }

      if (typeof blocked !== 'boolean') {
        errorMsg = 'Received invalid blocked from the /blocklist endpoint: ';
        errorMsg = errorMsg + total;
        console.error(errorMsg);
        reject({reason: errorMsg});
        return;
      }

      resolve({total: total, blocked: blocked});
    };

    request.ontimeout = function() {
      reject({reason: 'the blocklist HTTP request timed out'});
    };

    settings.then(function(settings) {
      request.open('GET', settings.serviceUrl + '/blocklist?uri=' + uri);
      request.send(null);
    });
  });

  p.uri = uri;
  return p;
}

/**
  * Make an HTTP request to the /blocklist endpoint and return a Promise that
  * resolves to the value of the response.
  *
  * This function can be called with the same uri multiple times consecutively
  * and it'll just keep returning the same Promise - won't make multiple HTTP
  * requests.
  *
  * But if you call the function with a different uri, then call it with the
  * first uri again, then it _will_ make another request for the first uri.
  *
  * Return a rejected Promise if the HTTP request times out, fails or is
  * invalid for any reason.
  *
  * Return a rejected Promise is the given uri is undefined.
  *
  * @param {String} uri The URI to be checked
  * @returns {Promise} A Promise that resolves to an object with three
  *   properties:
  *
  *   1. total: the number of annotations there are of this URI (Number)
  *   2. blocked: whether or not this URI is blocklisted (Boolean)
  *
  */
function getBlocklistIfUriHasChanged(uri) {
  if (!(blocklistPromise && blocklistPromise.uri === uri)) {
    blocklistPromise = getBlocklist(uri);
  }
  return blocklistPromise;
}

module.exports = getBlocklistIfUriHasChanged;
