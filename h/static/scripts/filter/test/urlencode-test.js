var angularMock = require('angular-mock');
var module = angularMock.module;
var inject = angularMock.inject;

var assert = chai.assert;
sinon.assert.expose(assert, {prefix: null});

describe('urlencode', function () {
  var filter = null;

  before(function () {
    angular.module('h', []).filter('urlencode', require('../urlencode'));
  });

  beforeEach(module('h'));

  beforeEach(inject(function ($filter) {
    filter = $filter('urlencode');
  }));

  it('encodes reserved characters in the term', function () {
    assert.equal(filter('#hello world'), '%23hello%20world');
  });
});
