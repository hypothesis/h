{inject, module} = angular.mock
sandbox = sinon.sandbox.create()

class MockSession
  login: (data, success, failure) ->
    success?(userid: 'alice')
    $promise:
      finally: sandbox.stub()
  register: (data, callback, errback) ->
    errback
      data:
        errors:
          username: 'taken'
        reason: 'registration error'
    $promise:
      finally: sandbox.stub()

mockFlash = info: sandbox.spy()
mockFormRespond = sandbox.spy()

describe 'h:AuthController', ->
  $scope = null
  $timeout = null
  auth = null
  session = null
  $controller = null

  before ->
    angular.module('h', [])
    .controller('AuthController', require('../auth-controller'))

  beforeEach module('h')
  beforeEach module('h.templates')

  beforeEach module ($provide) ->
    $provide.value '$timeout', sandbox.spy()
    $provide.value 'flash', mockFlash
    $provide.value 'session', new MockSession()
    $provide.value 'formRespond', mockFormRespond
    return

  beforeEach inject (_$controller_, $rootScope, _$timeout_, _session_) ->
    $scope = $rootScope.$new()
    $timeout = _$timeout_
    $controller = _$controller_
    auth = $controller 'AuthController', {$scope}
    session = _session_
    sandbox.spy session, 'login'

  afterEach ->
    sandbox.restore()

  describe '#submit()', ->
    it 'should call session methods on submit', ->

      auth.submit
        $name: 'login'
        $valid: true
        $setValidity: sandbox.stub()

      assert.called session.login

    it 'should do nothing when the form is invalid', ->
      auth.submit
        $name: 'login'
        $valid: false
        $setValidity: sandbox.stub()

      assert.notCalled session.login

    it 'should apply validation errors on submit', ->
      form =
        $name: 'register'
        $valid: true
        $setValidity: sandbox.stub()
        username:
          $setValidity: sandbox.stub()
        email:
          $setValidity: sandbox.stub()

      auth.submit(form)

      assert.calledWith mockFormRespond, form,
        {username: 'taken'},
        'registration error'

    it 'should apply reason-only validation errors from the server', ->
      # Make a mock session that returns an error response with a "reason" but
      # no "errors" in the JSON object.
      reason = 'Argh, crashed! :|'
      myMockSession = new MockSession()
      myMockSession.register = (data, callback, errback) ->
        errback({data: {reason: reason}})
        $promise: {finally: sandbox.stub()}

      # Get an AuthController object with our mock session.
      authCtrl = $controller(
        'AuthController', {$scope:$scope, session:myMockSession})

      form = {$name: 'register', $valid: true}

      authCtrl.submit(form)

      assert.calledWith(mockFormRespond, form, undefined, reason)

    it 'should handle invalid error responses from the server', ->
      # A mock session that returns an error that isn't a valid JSON object
      # in the form that the frontend expects. This happens if there's an
      # uncaught exception on the server.
      myMockSession = new MockSession()
      myMockSession.register = (data, callback, errback) ->
        errback('Oh no!!')
        $promise: {finally: sandbox.stub()}

      authCtrl = $controller(
        'AuthController', {$scope:$scope, session:myMockSession})

      form = {$name: 'register', $valid: true}

      authCtrl.submit(form)

      assert.calledWith(mockFormRespond, form, undefined,
        "Oops, something went wrong on the server. Please try again later!")

    it 'should emit an auth event once authenticated', ->
      form =
        $name: 'login'
        $valid: true
        $setValidity: sandbox.stub()

      sandbox.spy $scope, '$emit'

      auth.submit(form)
      assert.calledWith $scope.$emit, 'auth', null, userid: 'alice'

    it 'should emit an auth event if destroyed before authentication', ->
      sandbox.spy $scope, '$emit'
      $scope.$destroy()
      assert.calledWith $scope.$emit, 'auth', 'cancel'

  describe 'timeout', ->
    it 'should happen after a period of inactivity', ->
      sandbox.spy $scope, '$broadcast'
      $scope.form = $setPristine: sandbox.stub()
      $scope.model =
        username: 'test'
        email: 'test@example.com'
        password: 'secret'
        code: '1234'

      $scope.$digest()
      assert.called $timeout

      $timeout.lastCall.args[0]()
      assert.called $scope.form.$setPristine, 'the form is pristine'
      assert.deepEqual $scope.model, {}, 'the model is erased'
      assert.called mockFlash.info, 'a flash notification is shown'

    it 'should not happen if the model is empty', ->
      $scope.model = undefined
      $scope.$digest()
      assert.notCalled $timeout

      $scope.model = {}
      $scope.$digest()
      assert.notCalled $timeout
