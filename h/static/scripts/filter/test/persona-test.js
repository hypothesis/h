var module = angular.mock.module;
var inject = angular.mock.inject;

describe('persona', function () {
  var filter = null;
  var term = 'acct:hacker@example.com';

  before(function () {
    angular.module('h', []).filter('persona', require('../persona').filter);
  });

  beforeEach(module('h'));

  beforeEach(inject(function ($filter) {
    filter = $filter('persona');
  }));

  it('should return the requested part', function () {
    assert.equal(filter(term), 'hacker');
    assert.equal(filter(term, 'username'), 'hacker');
    assert.equal(filter(term, 'provider'), 'example.com');
  });

  it('should filter out invalid account IDs', function () {
    assert.equal(filter('bogus'), null);
    assert.equal(filter('bogus', 'username'), null);
    assert.notOk(filter('bogus', 'provider'), null);
  });
});
