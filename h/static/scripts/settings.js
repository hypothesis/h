'use strict';

var angular = require('angular');

/**
 * @ngdoc factory
 * @name  settings
 *
 * @description
 * The 'settings' factory exposes shared application settings, read from the
 * global variable 'hypothesis.settings' in the app page.
 */
// @ngInject
function settings($window) {
  var data = {};

  if ($window.hypothesis && $window.hypothesis.settings) {
    angular.copy($window.hypothesis.settings, data);
  }

  return data;
}

module.exports = settings;
