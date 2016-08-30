'use strict';

/**
 * Convert a `camelCase` or `CapitalCase` string to `kebab-case`
 */
function hyphenate(name) {
  var uppercasePattern = /([A-Z])/g;
  return name.replace(uppercasePattern, '-$1').toLowerCase();
}

/** Convert a `kebab-case` string to `camelCase` */
function unhyphenate(name) {
  var idx = name.indexOf('-');
  if (idx === -1) {
    return name;
  } else {
    var ch = (name[idx+1] || '').toUpperCase();
    return unhyphenate(name.slice(0,idx) + ch + name.slice(idx+2));
  }
}

module.exports = {
  hyphenate: hyphenate,
  unhyphenate: unhyphenate,
};
