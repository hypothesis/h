'use strict';

var urlUtil = require('../url-util');

describe('url-util', function () {
  describe('replaceURLParams()', function () {
    it('should replace params in URLs', function () {
      var replaced = urlUtil.replaceURLParams('http://foo.com/things/:id',
        {id: 'test'});
      assert.equal(replaced.url, 'http://foo.com/things/test');
    });

    it('should return unused params', function () {
      var replaced = urlUtil.replaceURLParams('http://foo.com/:id',
        {id: 'test', 'q': 'unused'});
      assert.deepEqual(replaced.params, {q: 'unused'});
    });
  });
});
