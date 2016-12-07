'use strict';

// ES2015 polyfills
require('core-js/es6/promise');
require('core-js/fn/array/find');
require('core-js/fn/array/find-index');
require('core-js/fn/array/from');
require('core-js/fn/array/includes');
require('core-js/fn/object/assign');
require('core-js/fn/string/starts-with');

// String.prototype.normalize()
// FIXME: This is a large polyfill which should be only loaded when necessary
require('unorm');

// Element.prototype.dataset, required by IE 10
require('element-dataset')();

// URL constructor, required by IE 10/11,
// early versions of Microsoft Edge.
try {
  new window.URL('https://hypothes.is');
} catch (err) {
  require('js-polyfills/url');
}

// KeyboardEvent.prototype.key
// (Native in Chrome >= 51, Firefox >= 23, IE >= 9)
require('keyboardevent-key-polyfill');

// Fetch API
// https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API
require('whatwg-fetch');
