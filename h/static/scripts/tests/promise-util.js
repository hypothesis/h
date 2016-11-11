'use strict';

/**
 * Takes a Promise<T> and returns a Promise<Result>
 * where Result = { result: T } | { error: any }.
 *
 * This is useful for testing that promises are rejected
 * as expected in tests.
 */
function toResult(promise) {
  return promise.then((result) => {
    return { result: result };
  }).catch((err) => {
    return { error: err };
  });
}

module.exports = {
  toResult: toResult,
};
