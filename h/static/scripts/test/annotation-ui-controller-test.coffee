{module, inject} = angular.mock

describe 'AnnotationUIController', ->
  $scope = null
  $rootScope = null
  annotationUI = null
  sandbox = null

  before ->
    angular.module('h', [])
    .controller('AnnotationUIController', require('../annotation-ui-controller'))

  beforeEach module('h')
  beforeEach inject ($controller, _$rootScope_) ->
    sandbox = sinon.sandbox.create()

    $rootScope = _$rootScope_
    $scope = $rootScope.$new()
    $scope.search = {}

    annotationUI =
      tool: 'comment'
      selectedAnnotationMap: null
      focusedAnnotationsMap: null
      removeSelectedAnnotation: sandbox.stub()

    $controller 'AnnotationUIController', {$scope, annotationUI}

  afterEach ->
    sandbox.restore()

  it 'updates the view when the selection changes', ->
    annotationUI.selectedAnnotationMap = {1: true, 2: true}
    $rootScope.$digest()
    assert.deepEqual($scope.selectedAnnotations, {1: true, 2: true})

  it 'updates the selection counter when the selection changes', ->
    annotationUI.selectedAnnotationMap = {1: true, 2: true}
    $rootScope.$digest()
    assert.deepEqual($scope.selectedAnnotationsCount, 2)

  it 'clears the selection when no annotations are selected', ->
    annotationUI.selectedAnnotationMap = {}
    $rootScope.$digest()
    assert.deepEqual($scope.selectedAnnotations, null)
    assert.deepEqual($scope.selectedAnnotationsCount, 0)

  it 'updates the focused annotations when the focus map changes', ->
    annotationUI.focusedAnnotationMap = {1: true, 2: true}
    $rootScope.$digest()
    assert.deepEqual($scope.focusedAnnotations, {1: true, 2: true})

  describe 'on annotationDeleted', ->
    it 'removes the deleted annotation from the selection', ->
      $rootScope.$emit('annotationDeleted', {id: 1})
      assert.calledWith(annotationUI.removeSelectedAnnotation, {id: 1})
