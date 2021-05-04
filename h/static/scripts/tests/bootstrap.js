'use strict';

// Polyfills needed only for PhantomJS, not any of our supported minimum
// browser versions.
require('core-js/features/array/find');
require('core-js/features/array/from');
require('core-js/features/array/includes');
require('core-js/features/object/assign');
require('core-js/features/promise');

// `Element.prototype.closest`
require('element-closest')(window);

// `String.prototype.normalize`
require('unorm');

// `fetch` and associated classes
require('whatwg-fetch');

// Expose the sinon assertions.
sinon.assert.expose(assert, { prefix: null });
