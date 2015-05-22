{inject, module} = require('angular-mock')

assert = chai.assert
sinon.assert.expose assert, prefix: null
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

# Return an AuthController instance and associated objects for tests to use.
_controller = (mocksession) ->
  controller = null
  $scope = null
  $timeout = null
  session = null
  mockFlash = info: sandbox.spy()
  mockFormRespond = sandbox.spy()
  inject(($controller, $rootScope) ->
    session = mocksession or new MockSession()
    $scope = $rootScope.$new()
    $timeout = sandbox.spy()
    params =
      $scope: $scope
      $timeout: $timeout
      flash: mockFlash
      session: session
      formRespond: mockFormRespond
    controller = $controller('AuthController', params)
  )
  return(
    auth: controller
    $scope: $scope
    $timeout: $timeout
    session: session
    mockFlash: mockFlash
    mockFormRespond: mockFormRespond
  )

describe 'h:AuthController', ->

  before ->
    angular.module('h', [])
    require('../auth-controller')

  beforeEach module('h')
  beforeEach module('h.templates')

  afterEach ->
    sandbox.restore()

  describe '#submit()', ->
    it 'should call session methods on submit', ->
      {auth, session} = _controller()
      sandbox.spy(session, 'login')

      auth.submit
        $name: 'login'
        $valid: true
        $setValidity: sandbox.stub()

      assert.called session.login

    it 'should do nothing when the form is invalid', ->
      {auth, session} = _controller()
      sandbox.spy(session, 'login')
      auth.submit
        $name: 'login'
        $valid: false
        $setValidity: sandbox.stub()

      assert.notCalled session.login

    it 'should apply validation errors on submit', ->
      {auth, mockFormRespond} = _controller()
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

      {auth, mockFormRespond} = _controller(myMockSession)

      form = {$name: 'register', $valid: true}

      auth.submit(form)

      assert.calledWith(mockFormRespond, form, undefined, reason)

    it 'should handle invalid error responses from the server', ->
      # A mock session that returns an error that isn't a valid JSON object
      # in the form that the frontend expects. This happens if there's an
      # uncaught exception on the server.
      myMockSession = new MockSession()
      myMockSession.register = (data, callback, errback) ->
        errback('Oh no!!')
        $promise: {finally: sandbox.stub()}

      {auth, mockFormRespond} = _controller(myMockSession)

      form = {$name: 'register', $valid: true}

      auth.submit(form)

      assert.calledWith(mockFormRespond, form, undefined,
        "Oops, something went wrong on the server. Please try again later!")

    it 'should emit an auth event once authenticated', ->
      {auth, $scope} = _controller()
      form =
        $name: 'login'
        $valid: true
        $setValidity: sandbox.stub()

      sandbox.spy $scope, '$emit'

      auth.submit(form)
      assert.calledWith $scope.$emit, 'auth', null, userid: 'alice'

    it 'should emit an auth event if destroyed before authentication', ->
      {$scope} = _controller()
      sandbox.spy $scope, '$emit'
      $scope.$destroy()
      assert.calledWith $scope.$emit, 'auth', 'cancel'

  describe 'timeout', ->
    it 'should happen after a period of inactivity', ->
      {$scope, $timeout, mockFlash} = _controller()
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
      {$scope, $timeout} = _controller()
      $scope.model = undefined
      $scope.$digest()
      assert.notCalled $timeout

      $scope.model = {}
      $scope.$digest()
      assert.notCalled $timeout
