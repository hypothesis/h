'use strict';

var stringUtil = require('../../util/string');

describe('util/string', function () {
  describe('hyphenate', function () {
    it('converts input to kebab-case', function () {
      assert.equal(stringUtil.hyphenate('fooBar'), 'foo-bar');
      assert.equal(stringUtil.hyphenate('FooBar'), '-foo-bar');
    });
  });

  describe('unhyphenate', function () {
    it('converts input to camelCase', function () {
      assert.equal(stringUtil.unhyphenate('foo-bar'), 'fooBar');
      assert.equal(stringUtil.unhyphenate('foo-bar-'), 'fooBar');
      assert.equal(stringUtil.unhyphenate('foo-bar-baz'), 'fooBarBaz');
      assert.equal(stringUtil.unhyphenate('-foo-bar-baz'), 'FooBarBaz');
    });
  });
});
