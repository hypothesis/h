// Minimal set of polyfills for PhantomJS 1.x under Karma.
// this Polyfills:
//
// - ES5
// - ES6 Promises
// - the DOM URL API

// Basic polyfills for APIs which are supported natively
// by all browsers we support (IE >= 10)
require('core-js/es5');

// Additional polyfills for newer features.
// Be careful that any polyfills used here match what is used in the
// app itself.
require('./polyfills');

// disallow console output during tests
['debug', 'log', 'warn', 'error'].forEach(function (method) {
  var realFn = window.console[method];
  window.console[method] = function () {
    var args = [].slice.apply(arguments);
    realFn.apply(console, args);
    throw new Error('Tests must not log console warnings');
  };
});
