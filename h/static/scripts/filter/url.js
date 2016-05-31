'use strict';

/**
 * URL encode a string, dealing appropriately with null values.
 */
function encode(str) {
  if (str) {
    return window.encodeURIComponent(str);
  }
  return '';
}

module.exports = {
  encode: encode,
};
