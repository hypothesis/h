/**
 * Feature flag client.
 *
 * This is a small utility which will periodically retrieve the application
 * feature flags from a JSON endpoint in order to expose these to the
 * client-side application.
 *
 * All feature flags implicitly start toggled off. When `flagEnabled` is first
 * called (or alternatively when `fetch` is called explicitly) an XMLHTTPRequest
 * will be made to retrieve the current feature flag values from the server.
 * Once these are retrieved, `flagEnabled` will return current values.
 *
 * If `flagEnabled` is called and the cache is more than `CACHE_TTL`
 * milliseconds old, then it will trigger a new fetch of the feature flag
 * values. Note that this is again done asynchronously, so it is only later
 * calls to `flagEnabled` that will return the updated values.
 *
 * Users of this service should assume that the value of any given flag can
 * change at any time and should write code accordingly. Feature flags should
 * not be cached, and should not be interrogated only at setup time.
 */
'use strict';

var assign = require('core-js/modules/$.assign');

var events = require('./events');

var CACHE_TTL = 5 * 60 * 1000; // 5 minutes

// @ngInject
function features ($document, $http, $log, $rootScope) {
  var cache = null;
  var featuresUrl = new URL('/app/features', $document.prop('baseURI')).href;
  var fetchOperation;

  $rootScope.$on(events.USER_CHANGED, function () {
    cache = null;
  });

  function fetch() {
    if (fetchOperation) {
      // fetch already in progress
      return fetchOperation;
    }

    fetchOperation = $http.get(featuresUrl).then(function (response) {
      cache = {
        updated: Date.now(),
        flags: response.data,
      };
    }).catch(function (err) {
      // if for any reason fetching features fails, we behave as
      // if all flags are turned off
      $log.warn('failed to fetch feature data', err);
      cache = assign({}, cache, {
        updated: Date.now(),
      });
    }).finally(function () {
      fetchOperation = null;
    });

    return fetchOperation;
  }

  function flagEnabled(name) {
    // Trigger a fetch if the cache is more than CACHE_TTL milliseconds old.
    // We don't wait for the fetch to complete, so it's not this call that
    // will see new data.
    if (!cache || (Date.now() - cache.updated) > CACHE_TTL) {
      fetch();
    }

    if (!cache || !cache.flags) {
      // a fetch is either in progress or fetching the feature flags
      // failed
      return false;
    }

    if (!cache.flags.hasOwnProperty(name)) {
      $log.warn('features service: looked up unknown feature:', name);
      return false;
    }
    return cache.flags[name];
  }

  return {
    fetch: fetch,
    flagEnabled: flagEnabled
  };
}

module.exports = features;
