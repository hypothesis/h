'use strict';

describe('annotationMapper', function() {
  var sandbox = sinon.sandbox.create();
  var $rootScope;
  var fakeStore;
  var fakeThreading;
  var annotationMapper;

  before(function () {
    angular.module('h', [])
    .service('annotationMapper', require('../annotation-mapper'));
  });

  beforeEach(angular.mock.module('h'));
  beforeEach(angular.mock.module(function ($provide) {
    fakeStore = {
      AnnotationResource: sandbox.stub().returns({})
    };
    fakeThreading = {
      idTable: {}
    };

    $provide.value('store', fakeStore);
    $provide.value('threading', fakeThreading);
  }));

  beforeEach(angular.mock.inject(function (_annotationMapper_, _$rootScope_) {
    $rootScope = _$rootScope_;
    annotationMapper = _annotationMapper_;
  }));

  afterEach(function () {
    sandbox.restore();
  });

  describe('.loadAnnotations()', function () {
    it('triggers the annotationLoaded event', function () {
      sandbox.stub($rootScope, '$emit');
      var annotations = [{id: 1}, {id: 2}, {id: 3}];
      annotationMapper.loadAnnotations(annotations);
      assert.called($rootScope.$emit);
      assert.calledWith($rootScope.$emit, 'annotationsLoaded', [{}, {}, {}]);
    });

    it('triggers the annotationUpdated event for each annotation in the threading cache', function () {
      sandbox.stub($rootScope, '$emit');
      var annotations = [{id: 1}, {id: 2}, {id: 3}];
      var cached = {message: {id: 1, $$tag: 'tag1'}};
      fakeThreading.idTable[1] = cached;

      annotationMapper.loadAnnotations(annotations);
      assert.called($rootScope.$emit);
      assert.calledWith($rootScope.$emit, 'annotationUpdated', cached.message);
    });

    it('replaces the properties on the cached annotation with those from the loaded one', function () {
      sandbox.stub($rootScope, '$emit');
      var annotations = [{id: 1, url: 'http://example.com'}];
      var cached = {message: {id: 1, $$tag: 'tag1'}};
      fakeThreading.idTable[1] = cached;

      annotationMapper.loadAnnotations(annotations);
      assert.called($rootScope.$emit);
      assert.calledWith($rootScope.$emit, 'annotationUpdated', {
        id: 1,
        url: 'http://example.com'
      });
    });

    it('excludes cached annotations from the annotationLoaded event', function () {
      sandbox.stub($rootScope, '$emit');
      var annotations = [{id: 1, url: 'http://example.com'}];
      var cached = {message: {id: 1, $$tag: 'tag1'}};
      fakeThreading.idTable[1] = cached;

      annotationMapper.loadAnnotations(annotations);
      assert.called($rootScope.$emit);
      assert.calledWith($rootScope.$emit, 'annotationsLoaded', []);
    });
  });

  describe('.unloadAnnotations()', function () {
    it('triggers the annotationDeleted event', function () {
      sandbox.stub($rootScope, '$emit');
      var annotations = [{id: 1}, {id: 2}, {id: 3}];
      annotationMapper.unloadAnnotations(annotations);
      assert.called($rootScope.$emit);
      assert.calledWith($rootScope.$emit, 'annotationDeleted', annotations[0]);
      assert.calledWith($rootScope.$emit, 'annotationDeleted', annotations[1]);
      assert.calledWith($rootScope.$emit, 'annotationDeleted', annotations[2]);
    });

    it('replaces the properties on the cached annotation with those from the deleted one', function () {
      sandbox.stub($rootScope, '$emit');
      var annotations = [{id: 1, url: 'http://example.com'}];
      var cached = {message: {id: 1, $$tag: 'tag1'}};
      fakeThreading.idTable[1] = cached;

      annotationMapper.unloadAnnotations(annotations);
      assert.called($rootScope.$emit);
      assert.calledWith($rootScope.$emit, 'annotationDeleted', {
        id: 1,
        url: 'http://example.com'
      });
    });
  });

  describe('.createAnnotation()', function () {
    it('creates a new annotaton resource', function () {
      var ann = {};
      fakeStore.AnnotationResource.returns(ann);
      var ret = annotationMapper.createAnnotation(ann);
      assert.equal(ret, ann);
    });

    it('creates a new resource with the new keyword', function () {
      var ann = {};
      fakeStore.AnnotationResource.returns(ann);
      annotationMapper.createAnnotation();
      assert.calledWithNew(fakeStore.AnnotationResource);
    });

    it('emits the "beforeAnnotationCreated" event', function () {
      sandbox.stub($rootScope, '$emit');
      var ann = {};
      fakeStore.AnnotationResource.returns(ann);
      annotationMapper.createAnnotation();
      assert.calledWith($rootScope.$emit, 'beforeAnnotationCreated', ann);
    });
  });

  describe('.deleteAnnotation()', function () {
    it('deletes the annotation on the server', function () {
      var p = Promise.resolve();
      var ann = {$delete: sandbox.stub().returns(p)};
      annotationMapper.deleteAnnotation(ann);
      assert.called(ann.$delete);
    });

    it('triggers the "annotationDeleted" event on success', function (done) {
      sandbox.stub($rootScope, '$emit');
      var p = Promise.resolve();
      var ann = {$delete: sandbox.stub().returns(p)};
      annotationMapper.deleteAnnotation(ann).then(function () {
        assert.called($rootScope.$emit);
        assert.calledWith($rootScope.$emit, 'annotationDeleted', ann);
      }).then(done, done);
      $rootScope.$apply();
    });

    it('does nothing on error', function (done) {
      sandbox.stub($rootScope, '$emit');
      var p = Promise.reject();
      var ann = {$delete: sandbox.stub().returns(p)};
      annotationMapper.deleteAnnotation(ann).catch(function () {
        assert.notCalled($rootScope.$emit);
      }).then(done, done);
      $rootScope.$apply();
    });

    it('return a promise that resolves to the deleted annotation', function (done) {
      var p = Promise.resolve();
      var ann = {$delete: sandbox.stub().returns(p)};
      annotationMapper.deleteAnnotation(ann).then(function (value) {
        assert.equal(value, ann);
      }).then(done, done);
      $rootScope.$apply();
    });
  });
});
