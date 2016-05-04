'use strict';

var angular = require('angular');
var EventEmitter = require('tiny-emitter');
var inherits = require('inherits');

function FakeRootThread() {
  this.thread = sinon.stub();
}
inherits(FakeRootThread, EventEmitter);

describe('AnnotationViewerController', function () {

  before(function () {
    angular.module('h', [])
      .controller('AnnotationViewerController',
        require('../annotation-viewer-controller'));
  });

  beforeEach(angular.mock.module('h'));

  // Return the $controller service from Angular.
  function getControllerService() {
    var $controller;
    angular.mock.inject(function (_$controller_) {
      $controller = _$controller_;
    }
    );
    return $controller;
  }

  function createAnnotationViewerController(opts) {
    var locals = {
      $location: opts.$location || {},
      $routeParams: opts.$routeParams || { id: 'test_annotation_id' },
      $scope: opts.$scope || {
        search: {},
      },
      annotationUI: {},
      rootThread: new FakeRootThread(),
      streamer: opts.streamer || { setConfig: function () {} },
      store: opts.store || {
        AnnotationResource: { get: sinon.spy() },
        SearchResource: { get: sinon.spy() }
      },
      streamFilter: opts.streamFilter || {
        setMatchPolicyIncludeAny: function () {
          return {
            addClause: function () {
              return {
                addClause: function () {}
              };
            }
          };
        },
        getFilter: function () {}
      },
      annotationMapper: opts.annotationMapper || { loadAnnotations: sinon.spy() },
    };
    inherits(locals.rootThread, EventEmitter);
    locals.ctrl = getControllerService()(
      'AnnotationViewerController', locals);
    return locals;
  }

  it('fetches the top-level annotation', function () {
    var controller = createAnnotationViewerController({});
    assert.calledOnce(controller.store.AnnotationResource.get);
    assert.calledWith(controller.store.AnnotationResource.get, { id: 'test_annotation_id' });
  });

  it('fetches any replies referencing the top-level annotation', function () {
    var controller = createAnnotationViewerController({});
    assert.calledOnce(controller.store.SearchResource.get);
    assert.calledWith(controller.store.SearchResource.get, { references: 'test_annotation_id' });
  });

  it('loads the top-level annotation and replies into annotationMapper', function () {
    var controller = createAnnotationViewerController({});
    assert.ok(controller.annotationMapper);
  });

  it('passes the annotations and replies from search into loadAnnotations', function () {
    var getAnnotation = sinon.stub().callsArgWith(1, { id: 'foo' });
    var getReferences = sinon.stub().callsArgWith(1, { rows: [{ id: 'bar' }, { id: 'baz' }] });

    var controller = createAnnotationViewerController({
      store: {
        AnnotationResource: { get: getAnnotation },
        SearchResource: { get: getReferences }
      }
    });
    var annotationMapper = controller.annotationMapper;

    assert.calledWith(annotationMapper.loadAnnotations, [{ id: 'foo' }]);
    assert.calledWith(annotationMapper.loadAnnotations, [{ id: 'bar' }, { id: 'baz' }]);
  });
});
