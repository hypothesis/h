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


function forEachSorted(obj, iterator, context) {
  var keys = Object.keys(obj).sort();
  for (var i = 0; i < keys.length; i++) {
    iterator.call(context, obj[keys[i]], keys[i]);
  }
  return keys;
}


function serializeValue(v) {
  if (angular.isObject(v)) {
    return angular.isDate(v) ? v.toISOString() : angular.toJson(v);
  }
  return v;
}


function encodeUriQuery(val) {
  return encodeURIComponent(val).replace(/%20/g, '+');
}


// Serialize an object containing parameters into a form suitable for a query
// string.
//
// This is an almost identical copy of the default Angular parameter serializer
// ($httpParamSerializer), with one important change. In Angular 1.4.x
// semicolons are not encoded in query parameter values. This is a problem for
// us as URIs around the web may well contain semicolons, which our backend will
// then proceed to parse as a delimiter in the query string. To avoid this
// problem we use a very conservative encoder, found above.
function serializeParams(params) {
  if (!params) return '';
  var parts = [];
  forEachSorted(params, function(value, key) {
    if (value === null || typeof value === 'undefined') return;
    if (angular.isArray(value)) {
      angular.forEach(value, function(v, k) {
        parts.push(encodeUriQuery(key)  + '=' + encodeUriQuery(serializeValue(v)));
      });
    } else {
      parts.push(encodeUriQuery(key) + '=' + encodeUriQuery(serializeValue(value)));
    }
  });

  return parts.join('&');
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
    paramSerializer: serializeParams,
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

      // N.B. in both cases below we explicitly override the default `get`
      // action because there is no way to provide defaultOptions to the default
      // action.
      instance.SearchResource = $resource(links.search.url, {}, {
        get: angular.extend({url: links.search.url}, defaultOptions),
      });

      instance.AnnotationResource = $resource(links.annotation.read.url, {}, {
        get: angular.extend(links.annotation.read, defaultOptions),
        create: angular.extend(links.annotation.create, defaultOptions),
        update: angular.extend(links.annotation.update, defaultOptions),
        delete: angular.extend(links.annotation.delete, defaultOptions),
      });

      return instance;
    });

  return instance;
}

module.exports = store;
