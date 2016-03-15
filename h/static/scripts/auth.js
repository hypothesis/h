'use strict';

/**
 * Provides functions for retrieving and caching API tokens required by
 * API requests and signing out of the API.
 */

var queryString = require('query-string');

var INITIAL_TOKEN = {
  // The user ID which the current cached token is valid for
  userid: undefined,
  // Promise for the API token for 'userid'.
  // This is initialized when fetchOrReuseToken() is called and
  // reset when signing out via logout()
  token: undefined,
};

var cachedToken = INITIAL_TOKEN;

/**
 * Fetches a new API token for the current logged-in user.
 *
 * @return {Promise} - A promise for a new JWT token.
 */
// @ngInject
function fetchToken($http, session, settings) {
  var tokenUrl = new URL('token', settings.apiUrl).href;
  var config = {
    params: {
      assertion: session.state.csrf,
    },
    // Skip JWT authorization for the token request itself.
    skipAuthorization: true,
    transformRequest: function (data) {
      return queryString.stringify(data);
    }
  };
  return $http.get(tokenUrl, config).then(function (response) {
    return response.data;
  });
}

/**
 * Fetches or returns a cached JWT API token for the current user.
 *
 * @return {Promise} - A promise for a JWT API token for the current
 *                     user.
 */
// @ngInject
function fetchOrReuseToken($http, jwtHelper, session, settings) {
  function refreshToken() {
    return fetchToken($http, session, settings).then(function (token) {
      return token;
    });
  }

  var userid;

  return session.load()
    .then(function (data) {
      userid = data.userid;
      if (userid === cachedToken.userid && cachedToken.token) {
        return cachedToken.token;
      } else {
        cachedToken = {
          userid: userid,
          token: refreshToken(),
        };
        return cachedToken.token;
      }
    })
    .then(function (token) {
      if (jwtHelper.isTokenExpired(token)) {
        cachedToken = {
          userid: userid,
          token: refreshToken(),
        };
        return cachedToken.token;
      } else {
        return token;
      }
    });
}

/**
 * JWT token fetcher function for use with 'angular-jwt'
 *
 * angular-jwt should be configured to use this function as its
 * tokenGetter implementation.
 */
// @ngInject
function tokenGetter($http, config, jwtHelper, session, settings) {
  // Only send the token on requests to the annotation storage service
  if (config.url.slice(0, settings.apiUrl.length) === settings.apiUrl) {
    return fetchOrReuseToken($http, jwtHelper, session, settings);
  } else {
    return null;
  }
}

function clearCache() {
  cachedToken = INITIAL_TOKEN;
}

// @ngInject
function authService(flash, session) {
  /**
   * Sign out from the API and clear any cached tokens.
   *
   * @return {Promise<void>} - A promise for when signout has completed.
   */
  function logout() {
    return session.logout({}).$promise
      .then(function() {
        clearCache();
      })
      .catch(function(err) {
        flash.error('Sign out failed!');
        throw err;
      });
  }

  return {
    logout: logout,
  };
}

module.exports = {
  tokenGetter: tokenGetter,
  clearCache: clearCache,
  service: authService,
};
