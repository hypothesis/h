"use strict";

var mock = require('angular-mock');

var assert = chai.assert;
sinon.assert.expose(assert, {prefix: null});


describe('h:features', function () {
  var $httpBackend;
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

  it('fetch should retrieve features data', function () {
    defaultHandler();
    features.fetch();
    $httpBackend.flush();
  });

  it('fetch should not explode for errors fetching features data', function () {
    defaultHandler().respond(500, "ASPLODE!");
    features.fetch();
    $httpBackend.flush();
  });

  it('flagEnabled should retrieve features data', function () {
    defaultHandler();
    features.flagEnabled('foo');
    $httpBackend.flush();
  });

  it('flagEnabled should return false initially', function () {
    defaultHandler();
    var result = features.flagEnabled('foo');
    $httpBackend.flush();

    assert.isFalse(result);
  });

  it('flagEnabled should return flag values when data is loaded', function () {
    defaultHandler();
    features.fetch();
    $httpBackend.flush();

    var foo = features.flagEnabled('foo');
    assert.isTrue(foo);

    var bar = features.flagEnabled('bar');
    assert.isFalse(bar);
  });

  it('flagEnabled should return false for unknown flags', function () {
    defaultHandler();
    features.fetch();
    $httpBackend.flush();

    var baz = features.flagEnabled('baz');
    assert.isFalse(baz);
  });

  it('flagEnabled should trigger a new fetch after cache expiry', function () {
    var clock = sandbox.useFakeTimers();

    defaultHandler();
    features.flagEnabled('foo');
    $httpBackend.flush();

    clock.tick(301 * 1000);

    defaultHandler();
    features.flagEnabled('foo');
    $httpBackend.flush();
  });
});
