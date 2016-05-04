EventEmitter = require('tiny-emitter')
inherits = require('inherits')

{module, inject} = angular.mock

class FakeRootThread extends EventEmitter
  constructor: () ->
    this.thread = sinon.stub()

describe 'StreamController', ->
  $controller = null
  $scope = null
  fakeAnnotationMapper = null
  fakeAnnotationUI = null
  fakeParams = null
  fakeQueryParser = null
  fakeRoute = null
  fakeStore = null
  fakeStreamer = null
  fakeStreamFilter = null
  fakeThreading = null

  sandbox = null

  createController = ->
    $controller('StreamController', {$scope: $scope})

  before ->
    angular.module('h', [])
    .controller('StreamController', require('../stream-controller'))

  beforeEach module('h')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()

    fakeAnnotationMapper = {
      loadAnnotations: sandbox.spy()
    }

    fakeAnnotationUI = {
      clearAnnotations: sandbox.spy()
      setCollapsed: sandbox.spy()
      setForceVisible: sandbox.spy()
    }

    fakeParams = {id: 'test'}

    fakeQueryParser = {
      populateFilter: sandbox.spy()
    }

    fakeRoute = {
      reload: sandbox.spy()
    }

    fakeSearchFilter = {
      generateFacetedFilter: sandbox.stub()
      toObject: sandbox.stub().returns({})
    }

    fakeStore = {
      SearchResource: {
        get: sandbox.spy()
      }
    }

    fakeStreamer = {
      open: sandbox.spy()
      close: sandbox.spy()
      setConfig: sandbox.spy()
    }

    fakeStreamFilter = {
      resetFilter: sandbox.stub().returnsThis()
      setMatchPolicyIncludeAll: sandbox.stub().returnsThis()
      getFilter: sandbox.stub()
    }

    fakeRootThread = new FakeRootThread()

    $provide.value 'annotationMapper', fakeAnnotationMapper
    $provide.value 'annotationUI', fakeAnnotationUI
    $provide.value '$route', fakeRoute
    $provide.value '$routeParams', fakeParams
    $provide.value 'queryParser', fakeQueryParser
    $provide.value 'rootThread', fakeRootThread
    $provide.value 'searchFilter', fakeSearchFilter
    $provide.value 'store', fakeStore
    $provide.value 'streamer', fakeStreamer
    $provide.value 'streamFilter', fakeStreamFilter
    return

  beforeEach inject (_$controller_, $rootScope) ->
    $controller = _$controller_
    $scope = $rootScope.$new()
    $scope.sort = {}

  afterEach ->
    sandbox.restore()

  it 'calls the search API with _separate_replies: true', ->
    createController()
    assert.equal(
      fakeStore.SearchResource.get.firstCall.args[0]._separate_replies, true)

  it 'passes the annotations and replies from search to loadAnnotations()', ->
    fakeStore.SearchResource.get = (query, func) ->
      func({
        'rows': ['annotation_1', 'annotation_2']
        'replies': ['reply_1', 'reply_2', 'reply_3']
      })

    createController()

    assert fakeAnnotationMapper.loadAnnotations.calledOnce
    assert fakeAnnotationMapper.loadAnnotations.calledWith(
      ['annotation_1', 'annotation_2'], ['reply_1', 'reply_2', 'reply_3']
    )


  describe 'on $routeUpdate', ->

    it 'reloads the route when the query changes', ->
      fakeParams.q = 'test query'
      createController()
      fakeParams.q = 'new query'
      $scope.$broadcast('$routeUpdate')
      assert.called(fakeAnnotationUI.clearAnnotations)
      assert.calledOnce(fakeRoute.reload)

    it 'does not reload the route when the query is the same', ->
      fakeParams.q = 'test query'
      createController()
      $scope.$broadcast('$routeUpdate')
      assert.notCalled(fakeRoute.reload)
