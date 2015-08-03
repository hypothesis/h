// @ngInject
function configureHttp($httpProvider) {
  // Use the Pyramid XSRF header name
  $httpProvider.defaults.xsrfHeaderName = 'X-CSRF-Token';
  // Use the JWT request interceptor
  $httpProvider.interceptors.push('jwtInterceptor');
}

module.exports = configureHttp;
