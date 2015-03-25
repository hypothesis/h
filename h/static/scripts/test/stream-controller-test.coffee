{module, inject} = require('angular-mock')

assert = chai.assert
sinon.assert.expose assert, prefix: null

describe 'StreamController', ->
  $scope = null
  fakeAnnotationMapper = null
  fakeQueryParser = null
  fakeRouteParams = null
  fakeSearchFilter = null
  fakeStore = null
  fakeStreamer = null
  fakeStreamFilter = null

  sandbox = null

  before ->
    angular.module('h', ['ngRoute'])
    .controller('StreamController', require('../stream-controller'))

  beforeEach module('h')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()

    fakeAnnotationMapper = {
      loadAnnotations: sandbox.spy()
    }

    fakeQueryParser = {
      populateFilter: sandbox.spy()
    }

    fakeRouteParams = {q: 'text:test'}

    fakeSearchFilter = {
      generateFacetedFilter: sandbox.spy()
      toObject: sandbox.spy()
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
      setMatchPolicyIncludeAll: sandbox.spy()
      resetFilter: sandbox.stub().returnsThis()
      getFilter: sandbox.spy()
    }

    $provide.value 'annotationMapper', fakeAnnotationMapper
    $provide.value 'queryParser', fakeQueryParser
    $provide.value '$routeParams', fakeRouteParams
    $provide.value 'searchFilter', fakeSearchFilter
    $provide.value 'store', fakeStore
    $provide.value 'streamer', fakeStreamer
    $provide.value 'streamFilter', fakeStreamFilter

    return

  createController = null

  beforeEach inject ($controller, $rootScope) ->
    $scope = $rootScope.$new()
    $scope.$digest = sinon.spy()
    $scope.threading = sinon.spy()
    $scope.search = {
      query: ''
    }
    $scope.lookup = {
      hasAnnotation: sinon.spy()
      getAnnotationContainers: sinon.spy()
    }
    $scope.sort = {
      name: 'Newest'
    }

    createController = ->
      controller = $controller('StreamController', {$scope: $scope})
      controller.threadRoot.children = []
      controller.idTable = {}
      controller

  afterEach ->
    sandbox.restore()

  describe '$routeParams', ->
    it 'gets populates the search query from routeParams.q', ->
      query = 'text:foo quote:bar user:john@doe'
      fakeRouteParams.q  = query
      createController()

      assert.equal $scope.search.query, query

  describe 'beforeAnnotationCreated', ->
    it 'puts the annotation within a container into $scope.threadRoot', ->
      annotation = {id: 'test', text: 'blabla'}
      createController()
      $scope.$emit 'beforeAnnotationCreated', annotation

      container = $scope.threadRoot.children[0]
      assert.isTrue container.message?
      assert.deepEqual container.message, annotation

  describe 'annotationCreated', ->
    it 'removes and reinserts the annotation from $scope.threadRoot', ->
      annotation1 = {id: 'test1', text: 'blabla'}
      annotation2 = {id: 'test2', text: 'blabla'}

      createController()
      $scope.$emit 'beforeAnnotationCreated', annotation1
      $scope.$emit 'beforeAnnotationCreated', annotation2

      container1 = $scope.threadRoot.children[0]
      container2 = $scope.threadRoot.children[1]

      assert.deepEqual container1.message, annotation1
      assert.deepEqual container2.message, annotation2

      annotation1.quote = 'more blabla'
      $scope.$emit 'annotationCreated', annotation1

      container1 = $scope.threadRoot.children[0]
      container2 = $scope.threadRoot.children[1]

      assert.deepEqual container1.message, annotation2
      assert.deepEqual container2.message, annotation1

  describe 'annotationDeleted', ->
    it 'removes the annotation container from $scope.threadRoot', ->
      annotation1 = {id: 'test1', text: 'blabla'}
      annotation2 = {id: 'test2', text: 'blabla'}

      createController()
      $scope.$emit 'beforeAnnotationCreated', annotation1
      $scope.$emit 'beforeAnnotationCreated', annotation2

      $scope.$emit 'annotationDeleted', annotation1
      container = $scope.threadRoot.children[0]
      assert.deepEqual container.message, annotation2

  describe 'annotationLoaded', ->
    it 'populates the annotations into $scope.threadRoot', ->
      annotation1 = {id: 'test1', text: 'blabla'}
      annotation2 = {id: 'test2', text: 'blabla'}

      createController()
      $scope.$emit 'annotationsLoaded', [annotation1, annotation2]

      container1 = $scope.threadRoot.children[0]
      container2 = $scope.threadRoot.children[1]

      assert.deepEqual container1.message, annotation1
      assert.deepEqual container2.message, annotation2

    it 'appends to the children, do not delete them', ->
      annotation1 = {id: 'test1', text: 'blabla'}
      annotation2 = {id: 'test2', text: 'blabla'}
      annotation3 = {id: 'test3', text: 'blabla'}

      createController()
      $scope.$emit 'beforeAnnotationCreated', annotation1
      $scope.$emit 'annotationsLoaded', [annotation2, annotation3]

      container1 = $scope.threadRoot.children[0]
      container2 = $scope.threadRoot.children[1]
      container3 = $scope.threadRoot.children[2]

      assert.deepEqual container1.message, annotation1
      assert.deepEqual container2.message, annotation2
      assert.deepEqual container3.message, annotation3
