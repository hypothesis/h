{module, inject} = angular.mock
events = require('../events')

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
  fakeGroups = null
  fakeRoute = null

  sandbox = null

  createController = (locals={}) ->
    locals.$scope = $scope
    $controller('AppController', locals)

  before ->
    angular.module('h', [])
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

    fakeGroups = {focus: sandbox.spy()}

    fakeRoute = {reload: sandbox.spy()}

    $provide.value 'annotationUI', fakeAnnotationUI
    $provide.value 'auth', fakeAuth
    $provide.value 'drafts', fakeDrafts
    $provide.value 'features', fakeFeatures
    $provide.value 'identity', fakeIdentity
    $provide.value 'session', fakeSession
    $provide.value 'groups', fakeGroups
    $provide.value '$route', fakeRoute
    $provide.value '$location', fakeLocation
    $provide.value '$routeParams', fakeParams
    return

  beforeEach inject (_$controller_, $rootScope) ->
    $controller = _$controller_
    $scope = $rootScope.$new()

  afterEach ->
    sandbox.restore()

  describe 'isSidebar property', ->

    it 'is false if the window is the top window', ->
      $window = {}
      $window.top = $window
      createController({$window})
      assert.isFalse($scope.isSidebar)

    it 'is true if the window is not the top window', ->
      $window = {top: {}}
      createController({$window})
      assert.isTrue($scope.isSidebar)

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

  it 'focuses the default group in logout', ->
    createController()
    {onlogout} = fakeIdentity.watch.args[0][0]
    onlogout()
    assert.calledWith(fakeGroups.focus, '__world__')

  it 'does not show login form for logged in users', ->
    createController()
    assert.isFalse($scope.accountDialog.visible)

  it 'does not show the share dialog at start', ->
    createController()
    assert.isFalse($scope.shareDialog.visible)

  it 'calls $route.reload() when the session state changes', ->
    createController()
    groupEvents = [events.SESSION_CHANGED, events.GROUP_FOCUSED];
    groupEvents.forEach((event) ->
      fakeRoute.reload = sinon.spy()
      $scope.$broadcast(event)
      assert.calledOnce(fakeRoute.reload)
    )
