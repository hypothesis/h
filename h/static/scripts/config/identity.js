var querystring = require('querystring');

var authPromise = null;
var tokenPromise = null;

var currentToken = null;


// @ngInject
function fetchToken($http, $q, jwtHelper, serviceUrl, session) {
  var tokenUrl = new URL('token', serviceUrl).href;

  if (currentToken === null || jwtHelper.isTokenExpired(currentToken)) {
    if (tokenPromise === null) {
      // Set up the token request data.
      var data = {
        assertion: session.state.csrf
      };

      // Skip JWT authorization for the token request itself.
      var config = {
        params: data,
        skipAuthorization: true,
        transformRequest: function (data) {
          return querystring.stringify(data);
        }
      };

      // Make the request.
      var request = $http.get(tokenUrl, config);

      // Extract and save the response data.
      tokenPromise = request.then(function (response) {
        tokenPromise = null;
        currentToken = response.data;
        return currentToken;
      });
    }

    // Return a promise of the access token.
    return tokenPromise;
  } else {
    // The token is available and not expired.
    return $q.when(currentToken);
  }
}


// @ngInject
function tokenGetter($injector, config, serviceUrl) {
  var requestUrl = config.url;

  // Only send the token on requests to the annotation storage service
  // and only if it is not the token request itself.
  if (requestUrl !== serviceUrl) {
    if (requestUrl.slice(0, serviceUrl.length) === serviceUrl) {
      return authPromise
        .then(function () {
          return $injector.invoke(fetchToken);
        })
        .catch(function () {
          return null;
        });
    }
  }

  return null;
}


// @ngInject
function checkAuthentication($injector, $q, session) {
  if (authPromise === null) {
    var deferred = $q.defer();
    authPromise = deferred.promise;

    session.load().$promise
      .then(function (data) {
        if (data.userid) {
          $injector.invoke(fetchToken).then(function (token) {
            deferred.resolve(token);
          });
        } else {
          deferred.reject('no session');
        }
      })
      .catch(function () {
        deferred.reject('request failure');
      });
  }

  return authPromise;
}


// @ngInject
function forgetAuthentication($q, flash, session) {
  return session.logout({}).$promise
    .then(function() {
      authPromise = $q.reject('no session');
      tokenPromise = null;
      currentToken = null;
      return null;
    })
    .catch(function(err) {
      flash.error('Sign out failed!');
      throw err;
    });
}


// @ngInject
function requestAuthentication($injector, $q, $rootScope) {
  return authPromise.catch(function () {
    var deferred = $q.defer();
    authPromise = deferred.promise;

    $rootScope.$on('auth', function(event, err, data) {
      if (err) {
        deferred.reject(err);
      } else {
        $injector.invoke(fetchToken).then(function (token) {
          deferred.resolve(token);
        });
      }
    });

    return authPromise;
  });
}


// @ngInject
function configureIdentity(identityProvider, jwtInterceptorProvider) {
  // Configure the identity provider.
  identityProvider.checkAuthentication = checkAuthentication;
  identityProvider.forgetAuthentication = forgetAuthentication;
  identityProvider.requestAuthentication = requestAuthentication;

  // Provide tokens from the token service to the JWT request interceptor.
  jwtInterceptorProvider.tokenGetter = tokenGetter;
}

module.exports = configureIdentity;
