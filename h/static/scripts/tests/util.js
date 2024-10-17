/* eslint-disable mocha/no-exports */
/**
 * Helper for writing parameterized tests.
 *
 * This is a wrapper around the `it()` function for creating a Mocha test case
 * which takes an array of fixture objects and calls it() once for each fixture,
 * passing in the fixture object as an argument to the test function.
 *
 * Usage:
 *   unroll('should return #output with #input', function (fixture) {
 *     assert.equal(functionUnderTest(fixture.input), fixture.output);
 *   },[
 *    {input: 'foo', output: 'bar'}
 *   ]);
 *
 * Based on https://github.com/lawrencec/Unroll with the following changes:
 *
 *  1. Support for test functions that return promises
 *  2. Mocha's `it()` is the only supported test function
 *  3. Fixtures are objects rather than arrays
 *
 * @param {string} description - Description with optional '#key' placeholders
 *        which are replaced by the values of the corresponding key from each
 *        fixture object.
 * @param {Function} testFn - Test function which can accept either `fixture`
 *        or `done, fixture` as arguments, where `done` is the callback for
 *        reporting completion of an async test and `fixture` is an object
 *        from the `fixtures` array.
 * @param {Array<T>} fixtures - Array of fixture objects.
 */
export function unroll(description, testFn, fixtures) {
  fixtures.forEach(fixture => {
    const caseDescription = Object.keys(fixture).reduce((desc, key) => {
      return desc.replace('#' + key, String(fixture[key]));
    }, description);
    it(caseDescription, done => {
      if (testFn.length === 1) {
        // Test case does not accept a 'done' callback argument, so we either
        // call done() immediately if it returns a non-Promiselike object
        // or when the Promise resolves otherwise
        const result = testFn(fixture);
        if (typeof result === 'object' && result.then) {
          result.then(() => {
            done();
          }, done);
        } else {
          done();
        }
      } else {
        // Test case accepts a 'done' callback argument and takes responsibility
        // for calling it when the test completes.
        testFn(done, fixture);
      }
    });
  });
}
