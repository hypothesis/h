{module, inject} = require('angular-mock')

assert = chai.assert
sinon.assert.expose assert, prefix: null


describe 'AnnotationViewerController', ->
  $scope = null
  $scope = null
  fakeAnnotationMapper = null
  fakeLocation = null
  fakeParams = null
  fakeStore = null
  fakeStreamer = null
  fakeStreamFilter = null
  fakeThreading = null

  sandbox = null

  before ->
    angular.module('h', ['ngRoute'])
    .controller('AnnotationViewerController', require('../annotation-viewer-controller'))

  beforeEach module('h')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()

    fakeAnnotationMapper = {
      loadAnnotations: sandbox.spy()
    }

    fakeLocation = {
      search: sandbox.stub().returns({})
    }

    fakeParams = {id: 'test'}

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
    $provide.value '$location', fakeLocation
    $provide.value '$routeParams', fakeParams
    $provide.value 'store', fakeStore
    $provide.value 'streamer', fakeStreamer
    $provide.value 'streamFilter', fakeStreamFilter
    $provide.value 'threading', fakeThreading
    return

  afterEach ->
    sandbox.restore()

  annotationViewerController = null

  beforeEach inject ($controller, $rootScope) ->
    $scope = $rootScope.$new()
    $scope.search = {}
    $scope.lookup = {}
    annotationViewerController = $controller 'AnnotationViewerController',
      $scope: $scope

  it 'sets the isEmbedded property to false', ->
    assert.isFalse($scope.isEmbedded)
