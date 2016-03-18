'use strict';

/**
 * Utility function for use with 'proxyquire' that prevents calls to
 * stubs 'calling through' to the _original_ dependency if a particular
 * function or property is not set on a stub, which is proxyquire's default
 * but usually undesired behavior.
 *
 * See https://github.com/thlorenz/proxyquireify#nocallthru
 *
 * Usage:
 *   var moduleUnderTest = proxyquire('./module-under-test', noCallThru({
 *     './dependency-foo': fakeFoo,
 *   }));
 *
 * @param {Object} stubs - A map of dependency paths to stubs, or a single
 *   stub.
 */
function noCallThru(stubs) {
  // This function is trivial but serves as documentation for why
  // '@noCallThru' is used.
  return Object.assign(stubs, {'@noCallThru':true});
}

module.exports = {
  noCallThru: noCallThru,
};
