'use strict';

// ES2015 polyfills
require('core-js/es6/promise');
require('core-js/fn/array/find');
require('core-js/fn/array/find-index');
require('core-js/fn/array/from');
require('core-js/fn/object/assign');

// URL constructor, required by IE 10/11,
// early versions of Microsoft Edge.
try {
  new window.URL('https://hypothes.is');
} catch (err) {
  require('js-polyfills/url');
}

// document.evaluate() implementation,
// required by IE 10, 11
//
// This sets `window.wgxpath`
if (!window.document.evaluate) {
  require('./vendor/wgxpath.install');
}
