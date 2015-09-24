{module, inject} = angular.mock

describe 'WidgetController', ->
  $scope = null
  fakeAnnotationMapper = null
  fakeAnnotationUI = null
  fakeAuth = null
  fakeCrossFrame = null
  fakeStore = null
  fakeStreamer = null
  fakeStreamFilter = null
  fakeThreading = null
  sandbox = null
  viewer = null

  before ->
    angular.module('h', [])
    .controller('WidgetController', require('../widget-controller.coffee'))

  beforeEach module('h')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()

    fakeAnnotationMapper = {loadAnnotations: sandbox.spy()}
    fakeAnnotationUI = {
      tool: 'comment'
      clearSelectedAnnotations: sandbox.spy()
    }
    fakeAuth = {user: null}
    fakeCrossFrame = {frames: []}

    fakeStore = {
      SearchResource:
        get: (query, callback) ->
          offset = query.offset or 0
          limit = query.limit or 20
          result =
            total: 100
            rows: [offset..offset+limit-1]

          callback result
    }

    fakeStreamer = {
      open: sandbox.spy()
      close: sandbox.spy()
      send: sandbox.spy()
    }

    fakeStreamFilter = {
      resetFilter: sandbox.stub().returnsThis()
      addClause: sandbox.stub().returnsThis()
      getFilter: sandbox.stub().returns({})
    }

    fakeThreading = {
      root: {}
    }

    $provide.value 'annotationMapper', fakeAnnotationMapper
    $provide.value 'annotationUI', fakeAnnotationUI
    $provide.value 'crossframe', fakeCrossFrame
    $provide.value 'store', fakeStore
    $provide.value 'streamer', fakeStreamer
    $provide.value 'streamFilter', fakeStreamFilter
    $provide.value 'threading', fakeThreading
    return

  beforeEach inject ($controller, $rootScope) ->
    $scope = $rootScope.$new()
    viewer = $controller 'WidgetController', {$scope}

  afterEach ->
    sandbox.restore()

  describe 'loadAnnotations', ->
    it 'loads all annotations for a frame', ->
      viewer.chunkSize = 20
      fakeCrossFrame.frames.push({uri: 'http://example.com'})
      $scope.$digest()
      loadSpy = fakeAnnotationMapper.loadAnnotations
      assert.callCount(loadSpy, 5)
      assert.calledWith(loadSpy, [0..19])
      assert.calledWith(loadSpy, [20..39])
      assert.calledWith(loadSpy, [40..59])
      assert.calledWith(loadSpy, [60..79])
      assert.calledWith(loadSpy, [80..99])

  describe 'shouldShowThread()', ->
    it 'returns false for orphan annotations', ->
      # Turn the 'show_unanchored_annotations' feature off.
      $scope.feature = -> false

      container =
        message:
          $orphan: true

      assert($scope.shouldShowThread(container) is false)

    it 'returns true for non-orphan annotations', ->
      # Turn the 'show_unanchored_annotations' feature off.
      $scope.feature = -> false

      container =
        message:
          $orphan: false

      assert($scope.shouldShowThread(container) is true)

    it 'returns true for orphan annotations if show_unanchored_annotations is on', ->
      # Turn the 'show_unanchored_annotations' feature on.
      $scope.feature = -> true

      container =
        message:
          $orphan: true

      assert($scope.shouldShowThread(container) is true)
