// this module is a wrapper around the 'ui.bootstrap' module which
// provides shims/stubs needed to use a current custom build of
// UI Bootstrap (which otherwise requires Angular 1.3.x) with Angular 1.2.x
//
// When/if the app is upgraded to Angular 1.3.x this module can
// just be removed.
var Promise = require('core-js/library/es6/promise');

module.exports = 'ui.bootstrap';

// import the upstream build of UI Bootstrap which defines the
// 'ui.bootstrap' module and sub-modules for the components we are using
require('./vendor/ui-bootstrap-custom-tpls-0.13.4');

angular.module('ui.bootstrap')
  // stub implementation of $templateRequest, which is used
  // by optional features that we are not using in the dropdown menu directive
  .factory('$templateRequest', function() {
    return function () {
      throw new Error('$templateRequest service is not implemented');
    }
  })
  .config(function ($provide) {
    // wrap the $animate service's addClass() and removeClass() functions
    // to return a Promise (as in Angular 1.3.x) instead of taking a done()
    // callback as the last argument (as in Angular 1.2.x)
    $provide.decorator('$animate', function($delegate) {
      return angular.extend({}, $delegate, {
        addClass: function (element, className) {
          return new Promise(function (resolve) {
            $delegate.addClass(element, className, resolve)
          });
        },

        removeClass: function (element, className) {
          return new Promise(function (resolve) {
            $delegate.removeClass(element, className, resolve);
          });
        }
      });
    });
  });
