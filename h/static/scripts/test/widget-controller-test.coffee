{module, inject} = angular.mock

events = require('../events')

describe 'WidgetController', ->
  $scope = null
  fakeAnnotationMapper = null
  fakeAnnotationUI = null
  fakeAuth = null
  fakeCrossFrame = null
  fakeDrafts = null
  fakeStore = null
  fakeStreamer = null
  fakeStreamFilter = null
  fakeThreading = null
  fakeGroups = null
  lastSearchResult = null
  sandbox = null
  viewer = null

  before ->
    angular.module('h', [])
    .controller('WidgetController', require('../widget-controller.coffee'))

  beforeEach module('h')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()

    fakeAnnotationMapper = {
      loadAnnotations: sandbox.spy()
      unloadAnnotations: sandbox.spy()
    }

    fakeAnnotationUI = {
      tool: 'comment'
      clearSelectedAnnotations: sandbox.spy()
    }
    fakeAuth = {user: null}
    fakeCrossFrame = {frames: []}
    fakeDrafts = {
      all: sandbox.stub()
    }

    lastSearchResult = null

    fakeStore = {
      SearchResource:
        get: (query, callback) ->
          offset = query.offset or 0
          limit = query.limit or 20
          result =
            total: 100
            rows: [offset..offset+limit-1]
          lastSearchResult = result
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
      root: {},
      thread: sandbox.stub()
    }

    fakeGroups = {
      focused: -> {id: 'foo'}
    }

    $provide.value 'annotationMapper', fakeAnnotationMapper
    $provide.value 'annotationUI', fakeAnnotationUI
    $provide.value 'crossframe', fakeCrossFrame
    $provide.value 'drafts', fakeDrafts
    $provide.value 'store', fakeStore
    $provide.value 'streamer', fakeStreamer
    $provide.value 'streamFilter', fakeStreamFilter
    $provide.value 'threading', fakeThreading
    $provide.value 'groups', fakeGroups
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

  describe 'when the focused group changes', ->
    it 'should load annotations for the new group', ->
      fakeThreading.annotationList = sandbox.stub().returns([{id: '1'}])
      fakeCrossFrame.frames.push({uri: 'http://example.com'})
      $scope.$broadcast(events.GROUP_FOCUSED)

      assert.calledWith(fakeAnnotationMapper.unloadAnnotations,
        [{id: '1'}])
      $scope.$digest();
      assert.calledWith(fakeAnnotationMapper.loadAnnotations,
        lastSearchResult.rows)
      assert.calledWith(fakeThreading.thread, fakeDrafts.all())
