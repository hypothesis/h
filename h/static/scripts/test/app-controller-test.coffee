{module, inject} = angular.mock

describe 'AppController', ->
  $controller = null
  $scope = null
  fakeAnnotationUI = null
  fakeAuth = null
  fakeDrafts = null
  fakeFeatures = null
  fakeIdentity = null
  fakeLocation = null
  fakeParams = null
  fakeSession = null

  sandbox = null

  createController = (locals={}) ->
    locals.$scope = $scope
    $controller('AppController', locals)

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
      userid: sandbox.stub()
    }

    fakeDrafts = {
      contains: sandbox.stub()
      remove: sandbox.spy()
      all: sandbox.stub().returns([])
      discard: sandbox.spy()
    }

    fakeFeatures = {
      fetch: sandbox.spy()
      flagEnabled: sandbox.stub().returns(false)
    }

    fakeIdentity = {
      watch: sandbox.spy()
      request: sandbox.spy()
    }

    fakeLocation = {
      search: sandbox.stub().returns({})
    }

    fakeParams = {id: 'test'}

    fakeSession = {}

    $provide.value 'annotationUI', fakeAnnotationUI
    $provide.value 'auth', fakeAuth
    $provide.value 'drafts', fakeDrafts
    $provide.value 'features', fakeFeatures
    $provide.value 'identity', fakeIdentity
    $provide.value 'session', fakeSession
    $provide.value '$location', fakeLocation
    $provide.value '$routeParams', fakeParams
    return

  beforeEach inject (_$controller_, $rootScope) ->
    $controller = _$controller_
    $scope = $rootScope.$new()

  afterEach ->
    sandbox.restore()

  describe 'isEmbedded property', ->

    it 'is false if the window is the top window', ->
      $window = {}
      $window.top = $window
      createController({$window})
      assert.isFalse($scope.isEmbedded)

    it 'is true if the window is not the top window', ->
      $window = {top: {}}
      createController({$window})
      assert.isTrue($scope.isEmbedded)

  it 'watches the identity service for identity change events', ->
    createController()
    assert.calledOnce(fakeIdentity.watch)

  it 'sets the user to null when the identity has been checked', ->
    createController()
    {onready} = fakeIdentity.watch.args[0][0]
    onready()
    assert.isNull($scope.auth.user)

  it 'sets auth.user to the authorized user at login', ->
    createController()
    fakeAuth.userid.withArgs('test-assertion').returns('acct:hey@joe')
    {onlogin} = fakeIdentity.watch.args[0][0]
    onlogin('test-assertion')
    assert.equal($scope.auth.user, 'acct:hey@joe')

  it 'sets auth.user to null at logout', ->
    createController()
    {onlogout} = fakeIdentity.watch.args[0][0]
    onlogout()
    assert.strictEqual($scope.auth.user, null)

  it 'does not show login form for logged in users', ->
    createController()
    assert.isFalse($scope.accountDialog.visible)

  it 'does not show the share dialog at start', ->
    createController()
    assert.isFalse($scope.shareDialog.visible)
