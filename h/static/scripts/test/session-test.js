"use strict";

var mock = angular.mock;

describe('h:session', function () {
  var $httpBackend;
  var fakeFlash;
  var fakeXsrf;
  var sandbox;
  var session;

  before(function () {
    angular.module('h', ['ngResource'])
    .service('session', require('../session'));
  });

  beforeEach(mock.module('h'));

  beforeEach(mock.module(function ($provide) {
    sandbox = sinon.sandbox.create();

    var fakeDocument = {
      prop: sandbox.stub()
    };
    fakeDocument.prop.withArgs('baseURI').returns('http://foo.com/');
    fakeFlash = {error: sandbox.spy()};

    $provide.value('$document', fakeDocument);
    $provide.value('flash', fakeFlash);
  }));


  beforeEach(mock.inject(function (_$httpBackend_, _session_) {
    $httpBackend = _$httpBackend_;
    session = _session_;
  }));

  afterEach(function () {
    $httpBackend.verifyNoOutstandingExpectation();
    $httpBackend.verifyNoOutstandingRequest();
    sandbox.restore();
  });

  // There's little point testing every single route here, as they're
  // declarative and ultimately we'd be testing ngResource.
  describe('#login()', function () {
    var url = 'http://foo.com/app?__formid__=login';

    it('should send an HTTP POST to the action', function () {
      $httpBackend.expectPOST(url, {code: 123}).respond({});
      session.login({code: 123});
      $httpBackend.flush();
    });

    it('should invoke the flash service with any flash messages', function () {
      var response = {
        flash: {
          error: ['fail']
        }
      };
      $httpBackend.expectPOST(url).respond(response);
      session.login({});
      $httpBackend.flush();
      assert.calledWith(fakeFlash.error, 'fail');
    });

    it('should assign errors and status reasons to the model', function () {
      var response = {
        model: {
          userid: 'alice'
        },
        errors: {
          password: 'missing'
        },
        reason: 'bad credentials'
      };
      $httpBackend.expectPOST(url).respond(response);
      var result = session.login({});
      $httpBackend.flush();
      assert.match(result, response.model, 'the model is present');
      assert.match(result.errors, response.errors, 'the errors are present');
      assert.match(result.reason, response.reason, 'the reason is present');
    });

    it('should capture and send the xsrf token', function () {
      var token = 'deadbeef';
      var headers = {
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json;charset=utf-8',
        'X-XSRF-TOKEN': token
      };
      var model = {csrf: token};
      $httpBackend.expectPOST(url).respond({model: model});
      session.login({});
      $httpBackend.flush();
      assert.equal(session.state.csrf, token);

      $httpBackend.expectPOST(url, {}, headers).respond({});
      session.login({});
      $httpBackend.flush();
    });

    it('should expose the model as session.state', function () {
      var response = {
        model: {
          userid: 'alice'
        }
      };
      assert.deepEqual(session.state, {});
      $httpBackend.expectPOST(url).respond(response);
      session.login({});
      $httpBackend.flush();
      assert.deepEqual(session.state, response.model);
    });

    it('an immediately-following call to #load() should not trigger a new request', function () {
      $httpBackend.expectPOST(url).respond({});
      session.login();
      $httpBackend.flush();

      session.load();
    });
  });

  describe('#load()', function () {
    var url = 'http://foo.com/app';

    it('should fetch the session data', function () {
      $httpBackend.expectGET(url).respond({});
      session.load();
      $httpBackend.flush();
    });

    it('should cache the session data', function () {
      $httpBackend.expectGET(url).respond({});
      session.load();
      session.load();
      $httpBackend.flush();
    });

    it('should eventually expire the cache', function () {
      var clock = sandbox.useFakeTimers();
      $httpBackend.expectGET(url).respond({});
      session.load();
      $httpBackend.flush();

      clock.tick(301 * 1000);

      $httpBackend.expectGET(url).respond({});
      session.load();
      $httpBackend.flush();
    });
  });
});
