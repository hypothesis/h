{module, inject} = angular.mock
events = require('../events')

describe 'AppController', ->
  $controller = null
  $scope = null
  $rootScope = null
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
  fakeWindow = null

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
      count: sandbox.stub().returns(0)
      unsaved: sandbox.stub().returns([])
    }

    fakeFeatures = {
      fetch: sandbox.spy()
      flagEnabled: sandbox.stub().returns(false)
    }

    fakeIdentity = {
      watch: sandbox.spy()
      request: sandbox.spy()
      logout: sandbox.stub()
    }

    fakeLocation = {
      search: sandbox.stub().returns({})
    }

    fakeParams = {id: 'test'}

    fakeSession = {}

    fakeGroups = {focus: sandbox.spy()}

    fakeRoute = {reload: sandbox.spy()}

    fakeWindow = {
      top: {}
      confirm: sandbox.stub()
    }

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
    $provide.value '$window', fakeWindow
    return

  beforeEach inject (_$controller_, _$rootScope_) ->
    $controller = _$controller_
    $rootScope = _$rootScope_
    $scope = $rootScope.$new()

  afterEach ->
    sandbox.restore()

  describe 'isSidebar property', ->

    it 'is false if the window is the top window', ->
      fakeWindow.top =  fakeWindow
      createController()
      assert.isFalse($scope.isSidebar)

    it 'is true if the window is not the top window', ->
      fakeWindow.top = {}
      createController()
      assert.isTrue($scope.isSidebar)

  it 'watches the identity service for identity change events', ->
    createController()
    assert.calledOnce(fakeIdentity.watch)

  it 'auth.status is "unknown" on startup', ->
    createController()
    assert.equal($scope.auth.status, 'unknown')

  it 'sets auth.status to "signed-out" when the identity has been checked but the user is not authenticated', ->
    createController()
    {onready} = fakeIdentity.watch.args[0][0]
    onready()
    assert.equal($scope.auth.status, 'signed-out')

  it 'sets auth.status to "signed-in" when the identity has been checked and the user is authenticated', ->
    createController()
    fakeAuth.userid.withArgs('test-assertion').returns('acct:hey@joe')
    {onlogin} = fakeIdentity.watch.args[0][0]
    onlogin('test-assertion')
    assert.equal($scope.auth.status, 'signed-in')

  it 'sets userid, username, and provider properties at login', ->
    createController()
    fakeAuth.userid.withArgs('test-assertion').returns('acct:hey@joe')
    {onlogin} = fakeIdentity.watch.args[0][0]
    onlogin('test-assertion')
    assert.equal($scope.auth.userid, 'acct:hey@joe')
    assert.equal($scope.auth.username, 'hey')
    assert.equal($scope.auth.provider, 'joe')

  it 'sets auth.status to "signed-out" at logout', ->
    createController()
    {onlogout} = fakeIdentity.watch.args[0][0]
    onlogout()
    assert.equal($scope.auth.status, "signed-out")

  it 'does not show login form for logged in users', ->
    createController()
    assert.isFalse($scope.accountDialog.visible)

  it 'does not show the share dialog at start', ->
    createController()
    assert.isFalse($scope.shareDialog.visible)

  it 'does not reload the view when the logged-in user changes on first load', ->
    createController()
    fakeRoute.reload = sinon.spy()
    $scope.$broadcast(events.USER_CHANGED, {initialLoad: true})
    assert.notCalled(fakeRoute.reload)

  it 'reloads the view when the logged-in user changes after first load', ->
    createController()
    fakeRoute.reload = sinon.spy()
    $scope.$broadcast(events.USER_CHANGED, {initialLoad: false})
    assert.calledOnce(fakeRoute.reload)

  describe 'on "beforeAnnotationCreated"', ->

    ###*
    #  It should clear any selection that exists in the sidebar before
    #  creating a new annotation. Otherwise the new annotation with its
    #  form open for the user to type in won't be visible because it's
    #  not part of the selection.
    ###
    it 'calls $scope.clearSelection()', ->
      createController()
      sandbox.spy($scope, 'clearSelection')

      $rootScope.$emit('beforeAnnotationCreated', {})

      assert.called($scope.clearSelection)

    it 'doesn\'t call $scope.clearSelection() when a highlight is created', ->
      createController()
      sandbox.spy($scope, 'clearSelection')

      $rootScope.$emit('beforeAnnotationCreated', {$highlight: true})

      assert.notCalled($scope.clearSelection)

  describe 'logout()', ->
    it 'prompts the user if there are drafts', ->
      fakeDrafts.count.returns(1)
      createController()

      $scope.logout()

      assert.equal(fakeWindow.confirm.callCount, 1)

    it 'emits "annotationDeleted" for each unsaved draft annotation', ->
      fakeDrafts.unsaved = sandbox.stub().returns(
        ["draftOne", "draftTwo", "draftThree"]
      )
      createController()
      $rootScope.$emit = sandbox.stub()

      $scope.logout()

      assert($rootScope.$emit.calledThrice)
      assert.deepEqual(
        $rootScope.$emit.firstCall.args, ["annotationDeleted", "draftOne"])
      assert.deepEqual(
        $rootScope.$emit.secondCall.args, ["annotationDeleted", "draftTwo"])
      assert.deepEqual(
        $rootScope.$emit.thirdCall.args, ["annotationDeleted", "draftThree"])

    it 'discards draft annotations', ->
      createController()

      $scope.logout()

      assert(fakeDrafts.discard.calledOnce)

    it 'does not emit "annotationDeleted" if the user cancels the prompt', ->
      createController()
      fakeDrafts.count.returns(1)
      $rootScope.$emit = sandbox.stub()
      fakeWindow.confirm.returns(false)

      $scope.logout()

      assert($rootScope.$emit.notCalled)

    it 'does not discard drafts if the user cancels the prompt', ->
      createController()
      fakeDrafts.count.returns(1)
      fakeWindow.confirm.returns(false)

      $scope.logout()

      assert(fakeDrafts.discard.notCalled)

    it 'does not prompt if there are no drafts', ->
      createController()
      fakeDrafts.count.returns(0)

      $scope.logout()

      assert.equal(fakeWindow.confirm.callCount, 0)
