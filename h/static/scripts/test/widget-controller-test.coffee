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
            replies: []

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

    $provide.value 'annotationMapper', fakeAnnotationMapper
    $provide.value 'annotationUI', fakeAnnotationUI
    $provide.value 'crossframe', fakeCrossFrame
    $provide.value 'store', fakeStore
    $provide.value 'streamer', fakeStreamer
    $provide.value 'streamFilter', fakeStreamFilter
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

    it 'passes annotations and replies from search to loadAnnotations()', ->
      fakeStore.SearchResource.get = (query, callback) ->
        callback({
          rows: ['annotation_1', 'annotation_2']
          replies: ['reply_1', 'reply_2', 'reply_3']
        })
      fakeCrossFrame.frames.push({uri: 'http://example.com'})
      $scope.$digest()

      assert fakeAnnotationMapper.loadAnnotations.calledOnce
      assert fakeAnnotationMapper.loadAnnotations.calledWith(
        ['annotation_1', 'annotation_2', 'reply_1', 'reply_2', 'reply_3']
      )
