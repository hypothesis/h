/**
 * A wrapper for the server's uriinfo endpoint.
 *
 * @module
 */
'use strict';

var settings = require('./settings');
var uriInfoPromise;


/**
 * Returns a new UriInfoError object, these errors are thrown if the uriinfo
 * HTTP request fails for any reason.
 *
 * @class
 */
function UriInfoError(message) {
  this.message = message;
}


/**
  * Make an HTTP request to the uriinfo endpoint and return a Promise that
  * resolves to the value of the response.
  *
  * This is a helper function for get() below, see that function's docstring
  * for details.
  *
  */
function getUriInfo(uri) {
  if (!uri) {
    return Promise.reject(new UriInfoError('uri was undefined'));
  }

  var p = new Promise(function(resolve, reject) {
    var request = new XMLHttpRequest();
    request.timeout = 1000;

    request.onload = function() {
      var info;
      var total;
      var blocked;
      var errorMsg;

      try {
        info = JSON.parse(this.responseText);
        total = info.total;
        blocked = info.blocked;
      } catch (e) {
        errorMsg = 'Received invalid JSON from the server: ';
        errorMsg = errorMsg + this.responseText;
        console.error(errorMsg);
        reject(new UriInfoError(errorMsg));
        return;
      }

      if (typeof total !== 'number') {
        errorMsg = 'Received invalid total from the server: ';
        errorMsg = errorMsg + total;
        console.error(errorMsg);
        reject(new UriInfoError(errorMsg));
        return;
      }

      if (typeof blocked !== 'boolean') {
        errorMsg = 'Received invalid blocked from the server: ';
        errorMsg = errorMsg + total;
        console.error(errorMsg);
        reject(new UriInfoError(errorMsg));
        return;
      }

      resolve({total: total, blocked: blocked});
    };

    request.ontimeout = function() {
      reject(new UriInfoError('the uriinfo HTTP request timed out'));
    };

    settings.then(function(settings) {
      request.open('GET', settings.serviceUrl + '/app/uriinfo?uri=' + uri);
      request.send(null);
    });
  });

  p.uri = uri;
  return p;
}

/**
 * Make an HTTP request to the server's uriinfo endpoint and return a Promise
 * that resolves to the response. Usage:
 *
 *     var uriInfo = require('uri-info');
 *
 *     uriInfo.get(uri).then(function(info) {
 *       ...
 *     });
 *
 * This function can be called with the same uri multiple times consecutively
 * and it'll just keep returning the same Promise - won't make multiple HTTP
 * requests.
 *
 * But if you call the function with a different uri, then call it with the
 * first uri again, then it _will_ make another request for the first uri.
 *
 * Also if the forceRefresh argument is true then it will always make a new
 * request.
 *
 * Returns a rejected Promise with a UriInfoError as its reason if the HTTP
 * request times out, fails or is invalid for any reason.
 *
 * Returns a rejected Promise with a UriInfoError as its reason if the given
 * uri is undefined.
 *
 * @param {String} uri The URI to be checked
 * @param {Boolean} forceRefresh Make a new HTTP request, even if the
 *   previously made request was for the same uri (optional, default: false)
 *
 * @returns {Promise} A Promise that resolves to an object with two properties:
 *   1. total:   the number of annotations there are of this URI (Number)
 *   2. blocked: whether or not this URI is blocklisted (Boolean)
 *
*/
function get(uri, forceRefresh) {
  forceRefresh = forceRefresh || false;

  if (forceRefresh || !(uriInfoPromise && uriInfoPromise.uri === uri)) {
    uriInfoPromise = getUriInfo(uri);
  }
  return uriInfoPromise;
}

module.exports = {
  get: get,
  UriInfoError: UriInfoError
};
