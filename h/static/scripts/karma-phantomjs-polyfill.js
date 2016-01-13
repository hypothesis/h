// minimal set of polyfills for PhantomJS 1.x under Karma.
// this Polyfills:
//
// - ES5
// - ES6 Promises
// - the DOM URL API

// basic polyfills for APIs which are supported natively
// by all browsers we support (IE >= 10)
require('js-polyfills/es5');
window.URL = require('js-polyfills/url').URL;

// additional polyfills for newer features.
// Be careful here that any added polyfills are consistent
// with what is used in builds of the app itself.
require('es6-promise');

// disallow console output during tests
['debug', 'log', 'warn', 'error'].forEach(function (method) {
  var realFn = window.console[method];
  window.console[method] = function () {
    var args = [].slice.apply(arguments);
    realFn.apply(console, args);
    throw new Error('Tests must not log console warnings');
  };
});
