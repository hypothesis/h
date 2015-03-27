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

mockFlash = info: sandbox.spy()
mockFormRespond = sandbox.spy()

describe 'h:AuthController', ->
  $scope = null
  $timeout = null
  auth = null
  session = null

  before ->
    angular.module('h', [])
    require('../auth-controller')

  beforeEach module('h')
  beforeEach module('h.templates')

  beforeEach module ($provide) ->
    $provide.value '$timeout', sandbox.spy()
    $provide.value 'flash', mockFlash
    $provide.value 'session', new MockSession()
    $provide.value 'formRespond', mockFormRespond
    return

  beforeEach inject ($controller, $rootScope, _$timeout_, _session_) ->
    $scope = $rootScope.$new()
    $timeout = _$timeout_
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
