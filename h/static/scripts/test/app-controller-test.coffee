{module, inject} = require('angular-mock')

assert = chai.assert
sinon.assert.expose assert, prefix: null


describe 'AppController', ->
  $controller = null
  $scope = null
  fakeAnnotationMapper = null
  fakeAnnotationUI = null
  fakeAuth = null
  fakeDrafts = null
  fakeIdentity = null
  fakeLocation = null
  fakeParams = null
  fakePermissions = null
  fakeStore = null
  fakeStreamer = null
  fakeStreamFilter = null
  fakeThreading = null

  sandbox = null

  createController = ->
    $controller('AppController', {$scope: $scope})

  before ->
    angular.module('h', ['ngRoute'])
    .controller('AppController', require('../app-controller'))
    .controller('AnnotationUIController', angular.noop)

  beforeEach module('h')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()

    fakeAnnotationMapper = {
      loadAnnotations: sandbox.spy()
    }

    fakeAnnotationUI = {
      tool: 'comment'
      clearSelectedAnnotations: sandbox.spy()
    }

    fakeAuth = {
      user: undefined
    }

    fakeDrafts = {
      remove: sandbox.spy()
      all: sandbox.stub().returns([])
      discard: sandbox.spy()
    }

    fakeIdentity = {
      watch: sandbox.spy()
      request: sandbox.spy()
    }

    fakeLocation = {
      search: sandbox.stub().returns({})
    }

    fakeParams = {id: 'test'}

    fakePermissions = {
      permits: sandbox.stub().returns(true)
    }

    fakeStore = {
      SearchResource: {
        get: sinon.spy()
      }
    }

    fakeStreamer = {
      open: sandbox.spy()
      close: sandbox.spy()
      send: sandbox.spy()
    }

    fakeStreamFilter = {
      setMatchPolicyIncludeAny: sandbox.stub().returnsThis()
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
    $provide.value 'auth', fakeAuth
    $provide.value 'drafts', fakeDrafts
    $provide.value 'identity', fakeIdentity
    $provide.value '$location', fakeLocation
    $provide.value '$routeParams', fakeParams
    $provide.value 'permissions', fakePermissions
    $provide.value 'store', fakeStore
    $provide.value 'streamer', fakeStreamer
    $provide.value 'streamfilter', fakeStreamFilter
    $provide.value 'threading', fakeThreading
    return

  beforeEach inject (_$controller_, $rootScope) ->
    $controller = _$controller_
    $scope = $rootScope.$new()
    $scope.$digest = sinon.spy()

  afterEach ->
    sandbox.restore()

  it 'does not show login form for logged in users', ->
    createController()
    assert.isFalse($scope.dialog.visible)

  describe 'applyUpdate', ->

    it 'calls annotationMapper.loadAnnotations() upon "create" action', ->
      createController()
      anns = ["my", "annotations"]
      fakeStreamer.onmessage
        type: "annotation-notification"
        options: action: "create"
        payload: anns
      assert.calledWith fakeAnnotationMapper.loadAnnotations, anns

    it 'calls annotationMapper.loadAnnotations() upon "update" action', ->
      createController()
      anns = ["my", "annotations"]
      fakeStreamer.onmessage
        type: "annotation-notification"
        options: action: "update"
        payload: anns
      assert.calledWith fakeAnnotationMapper.loadAnnotations, anns

    it 'calls annotationMapper.loadAnnotations() upon "past" action', ->
      createController()
      anns = ["my", "annotations"]
      fakeStreamer.onmessage
        type: "annotation-notification"
        options: action: "past"
        payload: anns
      assert.calledWith fakeAnnotationMapper.loadAnnotations, anns

    it 'looks up annotations at threading upon "delete" action', ->
      createController()
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
