'use strict';

var angular = require('angular');

var annotationUIFactory = require('../annotation-ui');
var events = require('../events');

describe('annotationMapper', function() {
  var sandbox = sinon.sandbox.create();
  var $rootScope;
  var annotationUI;
  var fakeStore;
  var annotationMapper;

  beforeEach(function () {
    fakeStore = {
      annotation: {
        delete: sinon.stub().returns(Promise.resolve({})),
      },
    };
    annotationUI = annotationUIFactory({});
    angular.module('app', [])
      .service('annotationMapper', require('../annotation-mapper'))
      .value('annotationUI', annotationUI)
      .value('store', fakeStore);
    angular.mock.module('app');

    angular.mock.inject(function (_$rootScope_, _annotationMapper_) {
      $rootScope = _$rootScope_;
      annotationMapper = _annotationMapper_;
    });
  });

  afterEach(function () {
    sandbox.restore();
  });

  describe('#loadAnnotations()', function () {
    it('triggers the annotationLoaded event', function () {
      sandbox.stub($rootScope, '$emit');
      var annotations = [{id: 1}, {id: 2}, {id: 3}];
      annotationMapper.loadAnnotations(annotations);
      assert.called($rootScope.$emit);
      assert.calledWith($rootScope.$emit, events.ANNOTATIONS_LOADED,
        [{id: 1}, {id: 2}, {id: 3}]);
    });

    it('also includes replies in the annotationLoaded event', function () {
      sandbox.stub($rootScope, '$emit');
      var annotations = [{id: 1}];
      var replies = [{id: 2}, {id: 3}];
      annotationMapper.loadAnnotations(annotations, replies);
      assert.called($rootScope.$emit);
      assert.calledWith($rootScope.$emit, events.ANNOTATIONS_LOADED,
        [{id: 1}, {id: 2}, {id: 3}]);
    });

    it('triggers the annotationUpdated event for each loaded annotation', function () {
      sandbox.stub($rootScope, '$emit');
      var annotations = [{id: 1}, {id: 2}, {id: 3}];
      annotationUI.addAnnotations(angular.copy(annotations));

      annotationMapper.loadAnnotations(annotations);
      assert.called($rootScope.$emit);
      assert.calledWith($rootScope.$emit, events.ANNOTATION_UPDATED,
        annotations[0]);
    });

    it('also triggers annotationUpdated for cached replies', function () {
      sandbox.stub($rootScope, '$emit');
      var annotations = [{id: 1}];
      var replies = [{id: 2}, {id: 3}, {id: 4}];
      annotationUI.addAnnotations([{id:3}]);

      annotationMapper.loadAnnotations(annotations, replies);
      assert($rootScope.$emit.calledWith(events.ANNOTATION_UPDATED,
        {id: 3}));
    });

    it('replaces the properties on the cached annotation with those from the loaded one', function () {
      sandbox.stub($rootScope, '$emit');
      var annotations = [{id: 1, url: 'http://example.com'}];
      annotationUI.addAnnotations([{id:1, $$tag: 'tag1'}]);

      annotationMapper.loadAnnotations(annotations);
      assert.called($rootScope.$emit);
      assert.calledWith($rootScope.$emit, events.ANNOTATION_UPDATED, {
        id: 1,
        url: 'http://example.com'
      });
    });

    it('excludes cached annotations from the annotationLoaded event', function () {
      sandbox.stub($rootScope, '$emit');
      var annotations = [{id: 1, url: 'http://example.com'}];
      annotationUI.addAnnotations([{id: 1, $$tag: 'tag1'}]);

      annotationMapper.loadAnnotations(annotations);
      assert.called($rootScope.$emit);
      assert.calledWith($rootScope.$emit, events.ANNOTATIONS_LOADED, []);
    });
  });

  describe('#unloadAnnotations()', function () {
    it('triggers the annotationsUnloaded event', function () {
      sandbox.stub($rootScope, '$emit');
      var annotations = [{id: 1}, {id: 2}, {id: 3}];
      annotationMapper.unloadAnnotations(annotations);
      assert.calledWith($rootScope.$emit,
        events.ANNOTATIONS_UNLOADED, annotations);
    });

    it('replaces the properties on the cached annotation with those from the deleted one', function () {
      sandbox.stub($rootScope, '$emit');
      var annotations = [{id: 1, url: 'http://example.com'}];
      annotationUI.addAnnotations([{id: 1, $$tag: 'tag1'}]);

      annotationMapper.unloadAnnotations(annotations);
      assert.calledWith($rootScope.$emit, events.ANNOTATIONS_UNLOADED, [{
        id: 1,
        url: 'http://example.com'
      }]);
    });
  });

  describe('#createAnnotation()', function () {
    it('creates a new annotation resource', function () {
      var ann = {};
      var ret = annotationMapper.createAnnotation(ann);
      assert.equal(ret, ann);
    });

    it('emits the "beforeAnnotationCreated" event', function () {
      sandbox.stub($rootScope, '$emit');
      var ann = {};
      annotationMapper.createAnnotation(ann);
      assert.calledWith($rootScope.$emit,
        events.BEFORE_ANNOTATION_CREATED, ann);
    });
  });

  describe('#deleteAnnotation()', function () {
    it('deletes the annotation on the server', function () {
      var ann = {id: 'test-id'};
      annotationMapper.deleteAnnotation(ann);
      assert.calledWith(fakeStore.annotation.delete, {id: 'test-id'});
    });

    it('triggers the "annotationDeleted" event on success', function (done) {
      sandbox.stub($rootScope, '$emit');
      var ann = {};
      annotationMapper.deleteAnnotation(ann).then(function () {
        assert.calledWith($rootScope.$emit,
          events.ANNOTATION_DELETED, ann);
      }).then(done, done);
      $rootScope.$apply();
    });

    it('does not emit an event on error', function (done) {
      sandbox.stub($rootScope, '$emit');
      fakeStore.annotation.delete.returns(Promise.reject());
      var ann = {id: 'test-id'};
      annotationMapper.deleteAnnotation(ann).catch(function () {
        assert.notCalled($rootScope.$emit);
      }).then(done, done);
      $rootScope.$apply();
    });
  });
});
