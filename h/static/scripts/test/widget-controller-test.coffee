{module, inject} = angular.mock

Promise = require('core-js/library/es6/promise')

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
  fakeGroups = null
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

    fakeGroups = {
      focused: -> {id: 'foo'},
      ready: -> Promise.resolve(),
    }

    $provide.value 'annotationMapper', fakeAnnotationMapper
    $provide.value 'annotationUI', fakeAnnotationUI
    $provide.value 'crossframe', fakeCrossFrame
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

    it.only 'should defer loading annotations until groups service is ready', ->
      ready = null
      groupsReady = new Promise((resolve) -> ready = resolve)
      fakeGroups.ready = -> groupsReady

      fakeCrossFrame.frames.push({uri: 'http://example.com'})
      $scope.$digest()
      assert.callCount(fakeAnnotationMapper.loadAnnotations, 0)
      ready()
      groupsReady.then(->
        assert.callCount(fakeAnnotationMapper.loadAnnotations, 1)
      )
