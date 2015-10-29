'use strict';

var mock = angular.mock;

var events = require('../events');

describe('h:features', function () {
  var $httpBackend;
  var $rootScope;
  var features;
  var sandbox;

  before(function () {
    angular.module('h', [])
    .service('features', require('../features'));
  });

  beforeEach(mock.module('h'));

  beforeEach(mock.module(function ($provide) {
    sandbox = sinon.sandbox.create();

    var fakeDocument = {
      prop: sandbox.stub()
    };
    fakeDocument.prop.withArgs('baseURI').returns('http://foo.com/');
    $provide.value('$document', fakeDocument);
  }));

  beforeEach(mock.inject(function ($injector) {
    $httpBackend = $injector.get('$httpBackend');
    $rootScope = $injector.get('$rootScope');
    features = $injector.get('features');
  }));

  afterEach(function () {
    $httpBackend.verifyNoOutstandingExpectation();
    $httpBackend.verifyNoOutstandingRequest();
    sandbox.restore();
  });

  function defaultHandler() {
    var handler = $httpBackend.expect('GET', 'http://foo.com/app/features');
    handler.respond(200, {foo: true, bar: false});
    return handler;
  }

  describe('fetch', function() {
    it('should retrieve features data', function () {
      defaultHandler();
      features.fetch();
      $httpBackend.flush();
      assert.equal(features.flagEnabled('foo'), true);
    });

    it('should return a promise', function () {
      defaultHandler();
      features.fetch().then(function () {
        assert.equal(features.flagEnabled('foo'), true);
      });
      $httpBackend.flush();
    });

    it('should not explode for errors fetching features data', function () {
      defaultHandler().respond(500, "ASPLODE!");
      var handler = sinon.stub();
      features.fetch().then(handler);
      $httpBackend.flush();
      assert.calledOnce(handler);
    });

    it('should only send one request at a time', function () {
      defaultHandler();
      features.fetch();
      features.fetch();
      $httpBackend.flush();
    });
  });

  describe('flagEnabled', function () {
    it('should retrieve features data', function () {
      defaultHandler();
      features.flagEnabled('foo');
      $httpBackend.flush();
    });

    it('should return false initially', function () {
      defaultHandler();
      var result = features.flagEnabled('foo');
      $httpBackend.flush();

      assert.isFalse(result);
    });

    it('should return flag values when data is loaded', function () {
      defaultHandler();
      features.fetch();
      $httpBackend.flush();

      var foo = features.flagEnabled('foo');
      assert.isTrue(foo);

      var bar = features.flagEnabled('bar');
      assert.isFalse(bar);
    });

    it('should return false for unknown flags', function () {
      defaultHandler();
      features.fetch();
      $httpBackend.flush();

      var baz = features.flagEnabled('baz');
      assert.isFalse(baz);
    });

    it('should trigger a new fetch after cache expiry', function () {
      var clock = sandbox.useFakeTimers();

      defaultHandler();
      features.flagEnabled('foo');
      $httpBackend.flush();

      clock.tick(301 * 1000);

      defaultHandler();
      features.flagEnabled('foo');
      $httpBackend.flush();
    });

    it('should clear the features data when the user changes', function () {
      // fetch features and check that the flag is set
      defaultHandler();
      features.fetch();
      $httpBackend.flush();
      assert.isTrue(features.flagEnabled('foo'));

      // simulate a change of logged-in user which should clear
      // the features cache
      $rootScope.$broadcast(events.USER_CHANGED, {});
      defaultHandler();
      assert.isFalse(features.flagEnabled('foo'));
      $httpBackend.flush();
    });
  });
});
