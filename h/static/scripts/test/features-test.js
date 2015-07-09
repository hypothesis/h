"use strict";

var mock = require('angular-mock');

var assert = chai.assert;
sinon.assert.expose(assert, {prefix: null});


describe('h:features', function () {
    var $httpBackend;
    var httpHandler;
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

        httpHandler = $httpBackend.when('GET', 'http://foo.com/app/features');
        httpHandler.respond(200, {foo: true, bar: false});
    }));

    afterEach(function () {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
        sandbox.restore();
    });

    it('fetch should retrieve features data', function () {
        $httpBackend.expect('GET', 'http://foo.com/app/features');
        features.fetch();
        $httpBackend.flush();
    });

    it('fetch should not explode for errors fetching features data', function () {
        httpHandler.respond(500, "ASPLODE!");
        features.fetch();
        $httpBackend.flush();
    });

    it('flagEnabled should retrieve features data', function () {
        $httpBackend.expect('GET', 'http://foo.com/app/features');
        features.flagEnabled('foo');
        $httpBackend.flush();
    });

    it('flagEnabled should return false initially', function () {
        var result = features.flagEnabled('foo');
        $httpBackend.flush();

        assert.isFalse(result);
    });

    it('flagEnabled should return flag values when data is loaded', function () {
        features.fetch();
        $httpBackend.flush();

        var foo = features.flagEnabled('foo');
        assert.isTrue(foo);

        var bar = features.flagEnabled('bar');
        assert.isFalse(bar);
    });

    it('flagEnabled should return false for unknown flags', function () {
        features.fetch();
        $httpBackend.flush();

        var baz = features.flagEnabled('baz');
        assert.isFalse(baz);
    });

    it('flagEnabled should trigger a new fetch after cache expiry', function () {
        var clock = sandbox.useFakeTimers();

        $httpBackend.expect('GET', 'http://foo.com/app/features');
        features.flagEnabled('foo');
        $httpBackend.flush();

        clock.tick(301 * 1000);

        $httpBackend.expect('GET', 'http://foo.com/app/features');
        features.flagEnabled('foo');
        $httpBackend.flush();
    });
});
