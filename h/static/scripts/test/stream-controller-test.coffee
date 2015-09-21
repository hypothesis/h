{module, inject} = angular.mock

describe 'StreamController', ->
  $controller = null
  $scope = null
  fakeAnnotationMapper = null
  fakeParams = null
  fakeRoute = null
  fakeStore = null
  fakeStreamer = null
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

    fakeParams = {id: 'test'}

    fakeRoute = {
      reload: sandbox.spy()
    }

    fakeStore = {
      SearchResource: {
        get: sandbox.spy()
      }
    }

    fakeStreamer = {
      open: sandbox.spy()
      close: sandbox.spy()
      send: sandbox.spy()
    }

    fakeThreading = {
      root: {}
    }

    $provide.value 'annotationMapper', fakeAnnotationMapper
    $provide.value '$route', fakeRoute
    $provide.value '$routeParams', fakeParams
    $provide.value 'store', fakeStore
    $provide.value 'streamer', fakeStreamer
    $provide.value 'threading', fakeThreading
    return

  beforeEach inject (_$controller_, $rootScope) ->
    $controller = _$controller_
    $scope = $rootScope.$new()
    $scope.sort = {}

  afterEach ->
    sandbox.restore()

  describe 'on $routeUpdate', ->

    it 'reloads the route when the query changes', ->
      fakeParams.q = 'test query'
      createController()
      fakeParams.q = 'new query'
      $scope.$broadcast('$routeUpdate')
      assert.calledOnce(fakeRoute.reload)

    it 'does not reload the route when the query is the same', ->
      fakeParams.q = 'test query'
      createController()
      $scope.$broadcast('$routeUpdate')
      assert.notCalled(fakeRoute.reload)
