{module, inject} = require('angular-mock')

assert = chai.assert
sinon.assert.expose assert, prefix: null


describe 'WidgetController', ->
  $scope = null
  fakeAnnotationMapper = null
  fakeAnnotationUI = null
  fakeCrossFrame = null
  fakeDrafts = null
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
    fakeCrossFrame = {providers: []}

    fakeDrafts = {remove: sandbox.spy()}

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
      idTable: {}
      register: (annotation) ->
        @idTable[annotation.id] = message: annotation
    }

    $provide.value 'annotationMapper', fakeAnnotationMapper
    $provide.value 'annotationUI', fakeAnnotationUI
    $provide.value 'crossframe', fakeCrossFrame
    $provide.value 'drafts', fakeDrafts
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

  describe 'streamer.onmessage', ->
    it 'calls annotationMapper.loadAnnotations() upon "create" action', ->
      anns = ["my", "annotations"]
      fakeStreamer.onmessage
        type: "annotation-notification"
        options: action: "create"
        payload: anns
      assert.calledWith fakeAnnotationMapper.loadAnnotations, anns

    it 'calls annotationMapper.loadAnnotations() upon "update" action', ->
      anns = ["my", "annotations"]
      fakeStreamer.onmessage
        type: "annotation-notification"
        options: action: "update"
        payload: anns
      assert.calledWith fakeAnnotationMapper.loadAnnotations, anns

    it 'calls annotationMapper.loadAnnotations() upon "past" action', ->
      anns = ["my", "annotations"]
      fakeStreamer.onmessage
        type: "annotation-notification"
        options: action: "past"
        payload: anns
      assert.calledWith fakeAnnotationMapper.loadAnnotations, anns

    it 'looks up annotations at threading upon "delete" action', ->
      $scope.$emit = sinon.spy()

      # Prepare the annotation that we have locally
      localAnnotation =
        id: "fake ID"
        data: "local data"

      # Introduce our annotation into threading
      fakeThreading.register localAnnotation

      # Prepare the annotation that will come "from the wire"
      remoteAnnotation =
        id: localAnnotation.id  # same id as locally
        data: "remote data"     # different data

      # Simulate a delete action
      fakeStreamer.onmessage
        type: "annotation-notification"
        options: action: "delete"
        payload: [ remoteAnnotation ]

      assert.calledWith $scope.$emit, "annotationDeleted", localAnnotation
