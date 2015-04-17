{module, inject} = require('angular-mock')

assert = chai.assert
sinon.assert.expose assert, prefix: null


describe 'AppController', ->
  $controller = null
  $scope = null
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
