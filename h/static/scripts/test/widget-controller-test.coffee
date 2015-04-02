{module, inject} = require('angular-mock')

assert = chai.assert
sinon.assert.expose assert, prefix: null


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
    fakeCrossFrame = {providers: []}

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
    it 'loads all annotation for a provider', ->
      viewer.chunkSize = 20
      fakeCrossFrame.providers.push {entities: ['http://example.com']}
      $scope.$digest()
      loadSpy = fakeAnnotationMapper.loadAnnotations
      assert.callCount(loadSpy, 5)
      assert.calledWith(loadSpy, [0..19])
      assert.calledWith(loadSpy, [20..39])
      assert.calledWith(loadSpy, [40..59])
      assert.calledWith(loadSpy, [60..79])
      assert.calledWith(loadSpy, [80..99])
