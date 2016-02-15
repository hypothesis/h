var inject = angular.mock.inject;
var module = angular.mock.module;

describe('h', function () {
  var auth = null;
  var fakeJwtHelper = null;
  var sandbox = null;

  before(function () {
    angular.module('h', [])
      .service('auth', require('../auth'));
  });

  beforeEach(function () {
    module('h');
  });

  beforeEach(module(function ($provide) {
    sandbox = sinon.sandbox.create();

    fakeJwtHelper = {
      decodeToken: sandbox.stub(),
      isTokenExpired: sandbox.stub()
    };

    $provide.value('jwtHelper', fakeJwtHelper);
  }));

  beforeEach(inject(function (_auth_) {
    auth = _auth_
  }));

  afterEach(function () {
    sandbox.restore()
  });

  it('returns the subject of a valid jwt', function () {
    var identity = 'fake-identity';
    fakeJwtHelper.isTokenExpired.withArgs(identity).returns(false);
    fakeJwtHelper.decodeToken.withArgs(identity).returns({sub: 'pandora'});
    var userid = auth.userid(identity);
    assert.equal(userid, 'pandora');
  });

  it('returns null for an expired jwt', function () {
    var identity = 'fake-identity';
    fakeJwtHelper.isTokenExpired.withArgs(identity).returns(true);
    var userid = auth.userid(identity);
    assert.isNull(userid);
  });

  it('returns null for an invalid jwt', function () {
    var identity = 'fake-identity';
    fakeJwtHelper.decodeToken.withArgs(identity).throws('Error');
    var userid = auth.userid(identity);
    assert.isNull(userid);
  });
});
