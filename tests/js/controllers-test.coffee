assert = chai.assert
sinon.assert.expose assert, prefix: null

fakeStore =
  SearchResource:
    get: sinon.spy()


describe 'h', ->
  $scope = null
  fakeAuth = null
  fakeIdentity = null
  fakeLocation = null
  fakeParams = null
  fakeStreamer = null
  sandbox = null

  beforeEach module('h')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()

    fakeAnnotator = {
      plugins: {
        Auth: {withToken: sandbox.spy()}
      }
      options: {}
      socialView: {name: 'none'}
      addPlugin: sandbox.spy()
    }

    fakeAuth = {
      user: null
    }

    fakeIdentity = {
      watch: sandbox.spy()
      request: sandbox.spy()
    }

    fakeLocation = {
      search: sandbox.stub().returns({})
    }
    fakeParams = {id: 'test'}
    fakeStreamer = {
      open: sandbox.spy()
      close: sandbox.spy()
      send: sandbox.spy()
    }

    $provide.value 'identity', fakeIdentity
    $provide.value 'streamer', fakeStreamer
    $provide.value '$location', fakeLocation
    $provide.value '$routeParams', fakeParams
    return

  afterEach ->
    sandbox.restore()

  describe 'AppController', ->
    createController = null

    beforeEach inject ($controller, $rootScope) ->
      $scope = $rootScope.$new()

      createController = ->
        $controller('AppController', {$scope: $scope})

    it 'does not show login form for logged in users', ->
      createController()
      assert.isFalse($scope.dialog.visible)

  describe 'AnnotationViewerController', ->
    annotationViewer = null

    beforeEach inject ($controller, $rootScope) ->
      $scope = $rootScope.$new()
      $scope.search = {}
      annotationViewer = $controller 'AnnotationViewerController',
        $scope: $scope
        store: fakeStore

    it 'sets the isEmbedded property to false', ->
      assert.isFalse($scope.isEmbedded)

describe 'AnnotationUIController', ->
  $scope = null
  $rootScope = null
  fakeAnnotationUI = null
  cacheAsyncQueue = null

  beforeEach module('h')
  beforeEach inject (_$rootScope_, AnnotationUIController) ->
    $rootScope = _$rootScope_
    $scope = $rootScope.$new()
    $scope.search = {}
    fakeAnnotationUI =
      tool: 'comment'
      selectedAnnotationMap: null
      focusedAnnotationsMap: null
      removeSelectedAnnotation: sandbox.stub()

    # FIXME: No idea why, but we cannot call $digest() here without angular
    # attempting to make an ajax request to an undefined url. This causes
    # an internal angular method to throw an exception as it tries to read
    # the url protocol. I'm assuming this is caused by a call to $evalAsync
    # somewhere in the application.
    cacheAsyncQueue = $rootScope.$$asyncQueue
    $rootScope.$$asyncQueue = []

    new AnnotationUIController(fakeAnnotationUI, $rootScope, $scope)

  afterEach -> $rootScope.$$asyncQueue = cacheAsyncQueue

  it 'updates the view when the selection changes', ->
    fakeAnnotationUI.selectedAnnotationMap = {1: true, 2: true}
    $rootScope.$digest()
    assert.deepEqual($scope.selectedAnnotations, {1: true, 2: true})

  it 'updates the selection counter when the selection changes', ->
    fakeAnnotationUI.selectedAnnotationMap = {1: true, 2: true}
    $rootScope.$digest()
    assert.deepEqual($scope.selectedAnnotationsCount, 2)

  it 'clears the selection when no annotations are selected', ->
    fakeAnnotationUI.selectedAnnotationMap = {}
    $rootScope.$digest()
    assert.deepEqual($scope.selectedAnnotations, null)
    assert.deepEqual($scope.selectedAnnotationsCount, 0)

  it 'updates the focused annotations when the focus map changes', ->
    fakeAnnotationUI.focusedAnnotationMap = {1: true, 2: true}
    $rootScope.$digest()
    assert.deepEqual($scope.focusedAnnotations, {1: true, 2: true})

  describe 'on annotationsLoaded', ->
    it 'enqueues a re-render of the current scope', ->
      target = sandbox.stub($scope, '$evalAsync')
      $rootScope.$emit('annotationsLoaded', [{}, {}, {}])
      assert.called(target)

  describe 'on getDocumentInfo', ->
    it 'enqueues a re-render of the current scope', ->
      target = sandbox.stub($scope, '$evalAsync')
      $rootScope.$emit('getDocumentInfo', [{}, {}, {}])
      assert.called(target)

  describe 'on annotationDeleted', ->
    it 'removes the deleted annotation from the selection', ->
      $rootScope.$emit('annotationDeleted', {id: 1})
      assert.calledWith(fakeAnnotationUI.removeSelectedAnnotation, {id: 1})
