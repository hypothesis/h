'use strict';

var angular = require('angular');

function prependTransform(defaults, transform) {
  // We can't guarantee that the default transformation is an array
  var result = angular.isArray(defaults) ? defaults.slice(0) : [defaults];
  result.unshift(transform);
  return result;
}

// stripInternalProperties returns a shallow clone of `obj`, lacking all
// properties that begin with a character that marks them as internal
// (currently '$' or '_');
function stripInternalProperties(obj) {
  var result = {};

  for (var k in obj) {
    if (obj.hasOwnProperty(k) && k[0] !== '$') {
      result[k] = obj[k];
    }
  }

  return result;
}

/**
 * @ngdoc factory
 * @name store
 * @description The `store` service handles the backend calls for the restful
 *              API. This is created dynamically from the document returned at
 *              API index so as to ensure that URL paths/methods do not go out
 *              of date.
 *
 *              The service currently exposes two resources:
 *
 *                store.SearchResource, for searching, and
 *                store.AnnotationResource, for CRUD operations on annotations.
 */
// @ngInject
function store($http, $resource, settings) {
  var instance = {};
  var defaultOptions = {
    transformRequest: prependTransform(
      $http.defaults.transformRequest,
      stripInternalProperties
    )
  };

  // We call the API root and it gives back the actions it provides.
  instance.$resolved = false;
  instance.$promise = $http.get(settings.apiUrl)
    .finally(function () { instance.$resolved = true; })
    .then(function (response) {
      var links = response.data.links;

      instance.SearchResource = $resource(links.search.url, {}, defaultOptions);

      instance.AnnotationResource = $resource(links.annotation.read.url, {}, {
        create: angular.extend(links.annotation.create, defaultOptions),
        update: angular.extend(links.annotation.update, defaultOptions),
        delete: angular.extend(links.annotation.delete, defaultOptions),
      });

      return instance;
    });

  return instance;
}

module.exports = store;
