'use strict';

var angular = require('angular');

var createFakeStore = require('./create-fake-store');

describe('AnnotationUIController', function () {
  var $scope;
  var $rootScope;
  var annotationUI;
  var sandbox;

  before(function () {
    angular.module('h', [])
      .controller('AnnotationUIController',
        require('../annotation-ui-controller'));
  });

  beforeEach(angular.mock.module('h'));
  beforeEach(angular.mock.inject(function ($controller, _$rootScope_) {
    sandbox = sinon.sandbox.create();

    $rootScope = _$rootScope_;
    $scope = $rootScope.$new();
    $scope.search = {};

    var store = createFakeStore({
      selectedAnnotationMap: null,
      focusedAnnotationsMap: null,
    });
    annotationUI = {
      removeSelectedAnnotation: sandbox.stub(),
      setState: store.setState,
      getState: store.getState,
      subscribe: store.subscribe,
    };

    $controller('AnnotationUIController', {
      $scope: $scope,
      annotationUI: annotationUI,
    });
  }));

  afterEach(function () {
    sandbox.restore();
  });

  it('updates the view when the selection changes', function () {
    annotationUI.setState({selectedAnnotationMap: { 1: true, 2: true }});
    assert.deepEqual($scope.selectedAnnotations, { 1: true, 2: true });
  });

  it('updates the selection counter when the selection changes', function () {
    annotationUI.setState({selectedAnnotationMap: { 1: true, 2: true }});
    assert.deepEqual($scope.selectedAnnotationsCount, 2);
  });

  it('clears the selection when no annotations are selected', function () {
    annotationUI.setState({selectedAnnotationMap: null});
    assert.deepEqual($scope.selectedAnnotations, null);
    assert.deepEqual($scope.selectedAnnotationsCount, 0);
  });

  it('updates the focused annotations when the focus map changes', function () {
    annotationUI.setState({focusedAnnotationMap: { 1: true, 2: true }});
    assert.deepEqual($scope.focusedAnnotations, { 1: true, 2: true });
  });

  describe('on annotationDeleted', function () {
    it('removes the deleted annotation from the selection', function () {
      $rootScope.$emit('annotationDeleted', { id: 1 });
      assert.calledWith(annotationUI.removeSelectedAnnotation, { id: 1 });
    });
  });
});
