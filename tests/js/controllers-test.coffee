assert = chai.assert
sinon.assert.expose assert, prefix: null

fakeStore =
  SearchResource:
    get: sinon.spy()


describe 'h', ->
  $scope = null
  fakeAuth = null
  fakeIdentity = null
  fakeLocation = null
  fakeParams = null
  fakeStreamer = null
  sandbox = null

  beforeEach module('h')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()

    fakeAnnotator = {
      plugins: {
        Auth: {withToken: sandbox.spy()}
      }
      options: {}
      socialView: {name: 'none'}
      addPlugin: sandbox.spy()
    }

    fakeAuth = {
      user: null
    }

    fakeIdentity = {
      watch: sandbox.spy()
      request: sandbox.spy()
    }

    fakeLocation = {
      search: sandbox.stub().returns({})
    }
    fakeParams = {id: 'test'}
    fakeStreamer = {
      open: sandbox.spy()
      close: sandbox.spy()
      send: sandbox.spy()
    }

    $provide.value 'annotator', fakeAnnotator
    $provide.value 'identity', fakeIdentity
    $provide.value 'streamer', fakeStreamer
    $provide.value '$location', fakeLocation
    $provide.value '$routeParams', fakeParams
    return

  afterEach ->
    sandbox.restore()

  describe 'AppController', ->
    createController = null

    beforeEach inject ($controller, $rootScope) ->
      $scope = $rootScope.$new()

      createController = ->
        $controller('AppController', {$scope: $scope})

    it 'does not show login form for logged in users', ->
      createController()
      $scope.$digest()
      assert.isFalse($scope.dialog.visible)

  describe 'AnnotationViewerController', ->
    annotationViewer = null

    beforeEach inject ($controller, $rootScope) ->
      $scope = $rootScope.$new()
      $scope.search = {}
      annotationViewer = $controller 'AnnotationViewerController',
        $scope: $scope
        store: fakeStore

    it 'sets the isEmbedded property to false', ->
      assert.isFalse($scope.isEmbedded)
