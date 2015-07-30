/**
 * @ngdoc service
 * @name  serviceUrl
 *
 * @description
 * The 'serviceUrl' exposes the base URL of the API backend.
 */
// @ngInject
function serviceUrl($document) {
  return $document
    .find('link')
    .filter(function () {
      return (this.rel === 'service' &&
              this.type === 'application/annotatorsvc+json');
    })
    .filter(function () {
      return this.href;
    })
    .prop('href');
}

module.exports = serviceUrl;
