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
