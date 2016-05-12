'use strict';

var angular = require('angular');

var annotationUIFactory = require('../annotation-ui');

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

    annotationUI = annotationUIFactory({});

    $controller('AnnotationUIController', {
      $scope: $scope,
      annotationUI: annotationUI,
    });
  }));

  afterEach(function () {
    sandbox.restore();
  });

  it('updates the view when the selection changes', function () {
    annotationUI.selectAnnotations(['1','2']);
    assert.deepEqual($scope.selectedAnnotations, { 1: true, 2: true });
  });

  it('updates the selection counter when the selection changes', function () {
    annotationUI.selectAnnotations(['1','2']);
    assert.deepEqual($scope.selectedAnnotationsCount, 2);
  });

  it('clears the selection when no annotations are selected', function () {
    annotationUI.selectAnnotations([]);
    assert.deepEqual($scope.selectedAnnotations, null);
    assert.deepEqual($scope.selectedAnnotationsCount, 0);
  });

  it('updates the focused annotations when the focus map changes', function () {
    annotationUI.focusAnnotations([
      {$$tag: '1'},
      {$$tag: '2'},
    ]);
    assert.deepEqual($scope.focusedAnnotations, { 1: true, 2: true });
  });

  describe('on annotationDeleted', function () {
    it('removes the deleted annotation from the selection', function () {
      annotationUI.selectAnnotations(['1']);
      $rootScope.$emit('annotationDeleted', { id: 1 });
      assert.equal(annotationUI.getState().selectedAnnotationMap, null);
    });
  });
});
