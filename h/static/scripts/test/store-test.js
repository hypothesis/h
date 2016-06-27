'use strict';

var angular = require('angular');
var proxyquire = require('proxyquire');

var util = require('./util');

describe('store', function () {
  var $httpBackend = null;
  var sandbox = null;
  var store = null;

  before(function () {
    angular.module('h')
    .service('store', proxyquire('../store', util.noCallThru({
      angular: angular,
      './retry-util': {
        retryPromiseOperation: function (fn) {
          return fn();
        },
      },
    })));
  });

  beforeEach(angular.mock.module('h'));

  beforeEach(angular.mock.module(function ($provide) {
    sandbox = sinon.sandbox.create();
    $provide.value('settings', {apiUrl: 'http://example.com/api'});
  }));

  afterEach(function () {
    $httpBackend.verifyNoOutstandingExpectation();
    $httpBackend.verifyNoOutstandingRequest();
    sandbox.restore();
  });

  beforeEach(angular.mock.inject(function (_$httpBackend_, _store_) {
    $httpBackend = _$httpBackend_;
    store = _store_;

    $httpBackend.expectGET('http://example.com/api').respond({
      links: {
         annotation: {
           create: {
             method: 'POST',
             url: 'http://example.com/api/annotations',
           },
           delete: {
             method: 'DELETE',
             url: 'http://example.com/api/annotations/:id',
           },
           read: {},
           update: {
             method: 'PUT',
             url: 'http://example.com/api/annotations/:id',
           },
         },
         search: {
           method: 'GET',
           url: 'http://example.com/api/search',
         },
      },
    });
    $httpBackend.flush();
  }));

  it('saves a new annotation', function () {
    store.annotation.create({}, {}).then(function (saved) {
      assert.isNotNull(saved.id);
    });
    $httpBackend.expectPOST('http://example.com/api/annotations')
    .respond(function () {
      return [201, {id: 'new-id'}, {}];
    });
    $httpBackend.flush();
  });

  it('updates an annotation', function () {
    store.annotation.update({id: 'an-id'}, {text: 'updated'});
    $httpBackend.expectPUT('http://example.com/api/annotations/an-id')
    .respond(function () {
      return [200, {}, {}];
    });
    $httpBackend.flush();
  });

  it('deletes an annotation', function () {
    store.annotation.delete({id: 'an-id'}, {});
    $httpBackend.expectDELETE('http://example.com/api/annotations/an-id')
    .respond(function () {
      return [200, {}, {}];
    });
    $httpBackend.flush();
  });

  it('removes internal properties before sending data to the server', function () {
    var annotation = {
      $highlight: true,
      $notme: 'nooooo!',
      allowed: 123
    };
    store.annotation.create({}, annotation);
    $httpBackend.expectPOST('http://example.com/api/annotations', {
      allowed: 123
    })
    .respond(function () { return {id: 'test'}; });
    $httpBackend.flush();
  });

  // Our backend service interprets semicolons as query param delimiters, so we
  // must ensure to encode them in the query string.
  it('encodes semicolons in query parameters', function () {
    store.search({'uri': 'http://example.com/?foo=bar;baz=qux'});
    $httpBackend.expectGET('http://example.com/api/search?uri=http%3A%2F%2Fexample.com%2F%3Ffoo%3Dbar%3Bbaz%3Dqux')
    .respond(function () { return [200, {}, {}]; });
    $httpBackend.flush();
  });
});
