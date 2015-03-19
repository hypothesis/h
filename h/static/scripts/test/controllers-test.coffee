{module, inject} = require('angular-mock')

assert = chai.assert
sinon.assert.expose assert, prefix: null


describe 'h:controllers', ->
  before ->
    angular.module('h', ['ngRoute'])
    require('../controllers')

  describe 'AppController', ->
    $scope = null
    fakeAnnotationMapper = null
    fakeAnnotationUI = null
    fakeAuth = null
    fakeDrafts = null
    fakeIdentity = null
    fakeHost = null
    fakeLocation = null
    fakeParams = null
    fakePermissions = null
    fakeStore = null
    fakeStreamer = null
    fakeStreamFilter = null
    fakeThreading = null

    sandbox = null

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

      fakeHost = {
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
      $provide.value 'host', fakeHost
      $provide.value '$location', fakeLocation
      $provide.value '$routeParams', fakeParams
      $provide.value 'permissions', fakePermissions
      $provide.value 'store', fakeStore
      $provide.value 'streamer', fakeStreamer
      $provide.value 'streamfilter', fakeStreamFilter
      $provide.value 'threading', fakeThreading
      return

    afterEach ->
      sandbox.restore()

    describe 'AppController', ->
      createController = null

      beforeEach inject ($controller, $rootScope) ->
        $scope = $rootScope.$new()
        $scope.$digest = sinon.spy()

        createController = ->
          $controller('AppController', {$scope: $scope})

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

    describe 'AnnotationViewerController', ->
      annotationViewer = null

      beforeEach inject ($controller, $rootScope) ->
        $scope = $rootScope.$new()
        $scope.search = {}
        annotationViewer = $controller 'AnnotationViewerController',
          $scope: $scope

      it 'sets the isEmbedded property to false', ->
        assert.isFalse($scope.isEmbedded)

  describe 'ViewerController', ->
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
      $provide.value 'auth', fakeAuth
      $provide.value 'crossframe', fakeCrossFrame
      $provide.value 'store', fakeStore
      $provide.value 'streamer', fakeStreamer
      $provide.value 'streamfilter', fakeStreamFilter
      return

    beforeEach inject ($controller, $rootScope) ->
      $scope = $rootScope.$new()
      viewer = $controller 'ViewerController', {$scope}

    afterEach ->
      sandbox.restore()

    describe 'loadAnnotations', ->
      it 'loads all annotation for a provider', ->
        fakeCrossFrame.providers.push {entities: ['http://example.com']}
        $scope.$digest()
        loadSpy = fakeAnnotationMapper.loadAnnotations
        assert.callCount(loadSpy, 5)
        assert.calledWith(loadSpy, [0..19])
        assert.calledWith(loadSpy, [20..39])
        assert.calledWith(loadSpy, [40..59])
        assert.calledWith(loadSpy, [60..79])
        assert.calledWith(loadSpy, [80..99])

  describe 'AnnotationUIController', ->
    $scope = null
    $rootScope = null
    annotationUI = null
    sandbox = null

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
