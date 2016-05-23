'use strict';

var memoize = require('../memoize');

describe('memoize', function () {
  var count = 0;
  var memoized;

  function square(arg) {
    ++count;
    return arg * arg;
  }

  beforeEach(function () {
    count = 0;
    memoized = memoize(square);
  });

  it('computes the result of the function', function () {
    assert.equal(memoized(12), 144);
  });

  it('does not recompute if the input is unchanged', function () {
    memoized(42);
    memoized(42);
    assert.equal(count, 1);
  });

  it('recomputes if the input changes', function () {
    memoized(42);
    memoized(39);
    assert.equal(count, 2);
  });
});
