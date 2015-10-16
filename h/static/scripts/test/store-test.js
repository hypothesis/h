'use strict';

var inject = angular.mock.inject;
var module = angular.mock.module;

describe('store', function () {
  var $httpBackend = null;
  var sandbox = null;
  var store = null;

  before(function () {
    angular.module('h', ['ngResource'])
    .service('store', require('../store'));
  });

  beforeEach(module('h'));

  beforeEach(module(function ($provide) {
    sandbox = sinon.sandbox.create();
    $provide.value('settings', {apiUrl: 'http://example.com/api'});
  }));

  afterEach(function () {
    $httpBackend.verifyNoOutstandingExpectation();
    $httpBackend.verifyNoOutstandingRequest();
    sandbox.restore();
  });

  beforeEach(inject(function ($q, _$httpBackend_, _store_) {
    $httpBackend = _$httpBackend_;
    store = _store_;

    $httpBackend.expectGET('http://example.com/api').respond({
      links: {
         annotation: {
           create: {
             method: 'POST',
             url: 'http://example.com/api/annotations',
           },
           delete: {},
           read: {},
           update: {},
         },
         search: {
           url: 'http://0.0.0.0:5000/api/search',
         },
      },
    });
    $httpBackend.flush();
  }));

  it('reads the operations from the backend', function () {
    assert.isFunction(store.AnnotationResource, 'expected store.AnnotationResource to be a function')
    assert.isFunction(store.SearchResource, 'expected store.SearchResource to be a function')
  });

  it('saves a new annotation', function () {
    var annotation = new store.AnnotationResource({id: 'test'});
    var saved = {};

    annotation.$create().then(function () {
      assert.isNotNull(saved.id);
    });

    $httpBackend.expectPOST('http://example.com/api/annotations', {id: 'test'})
    .respond(function () {
      saved.id = annotation.id;
      return [201, {}, {}];
    });
    $httpBackend.flush();
  });

  it('removes internal properties before sending data to the server', function () {
    var annotation = new store.AnnotationResource({
      $highlight: true,
      $notme: 'nooooo!',
      allowed: 123
    });
    annotation.$create();
    $httpBackend.expectPOST('http://example.com/api/annotations', {
      allowed: 123
    })
    .respond(function () { return {id: 'test'}; });
    $httpBackend.flush();
  });
});
