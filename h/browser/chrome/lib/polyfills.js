// Polyfills for APIs which are not present on all supported
// versions of Chrome

// polyfill for the fetch() API for Chrome < 42,
// also used by our PhantomJS tests
require('whatwg-fetch');
