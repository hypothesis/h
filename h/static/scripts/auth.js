/**
 * @ngdoc service
 * @name  auth
 *
 * @description
 * The 'auth' service exposes authorization helpers for other components.
 */
// @ngInject
function Auth(jwtHelper) {
  this.userid = function userid(identity) {
    try {
      if (jwtHelper.isTokenExpired(identity)) {
        return null;
      } else {
        var payload = jwtHelper.decodeToken(identity);
        return payload.sub || null;
      }
    } catch (error) {
      return null;
    }
  };
}

module.exports = Auth;
