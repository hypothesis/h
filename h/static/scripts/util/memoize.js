'use strict';

/**
 * A simple memoization function which caches the last result of
 * a single-argument function.
 *
 * The argument to the input function may be of any type and is compared
 * using reference equality.
 */
function memoize(fn) {
  if (fn.length !== 1) {
    throw new Error('Memoize input must be a function of one argument');
  }

  var lastArg;
  var lastResult;

  return function (arg) {
    if (arg === lastArg) {
      return lastResult;
    }
    lastArg = arg;
    lastResult = fn(arg);
    return lastResult;
  };
}

module.exports = memoize;
