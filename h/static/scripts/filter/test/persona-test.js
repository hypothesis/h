var module = angular.mock.module;
var inject = angular.mock.inject;

describe('persona', function () {
  var filter = null;
  var term = 'acct:hacker@example.com';

  before(function () {
    angular.module('h', []).filter('persona', require('../persona'));
  });

  beforeEach(module('h'));

  beforeEach(inject(function ($filter) {
    filter = $filter('persona');
  }));

  it('should return the whole term by request', function () {
    var result = filter('acct:hacker@example.com', 'term');
    assert.equal(result, 'acct:hacker@example.com');
  });

  it('should return the requested part', function () {
    assert.equal(filter(term), 'hacker');
    assert.equal(filter(term, 'term'), term);
    assert.equal(filter(term, 'username'), 'hacker');
    assert.equal(filter(term, 'provider'), 'example.com');
  });

  it('should pass unrecognized terms as username or term', function () {
    assert.equal(filter('bogus'), 'bogus');
    assert.equal(filter('bogus', 'username'), 'bogus');
  });

  it('should handle error cases', function () {
    assert.notOk(filter());
    assert.notOk(filter('bogus', 'provider'));
  });
});
