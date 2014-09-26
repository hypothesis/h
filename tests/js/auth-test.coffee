assert = chai.assert
sinon.assert.expose assert, prefix: null
sandbox = sinon.sandbox.create()


class MockSession
  login: sandbox.stub()
  register: (data, callback, errback) ->
    errback
      data:
        errors:
          username: 'taken'
        reason: 'registration error'

mockFlash = sandbox.spy()
mockFormHelpers = applyValidationErrors: sandbox.spy()

describe 'h.auth', ->
  beforeEach module('h.auth')
  beforeEach module('h.templates')

  beforeEach module ($provide) ->
    $provide.value '$timeout', sandbox.spy()
    $provide.value 'flash', mockFlash
    $provide.value 'session', new MockSession()
    $provide.value 'formHelpers', mockFormHelpers
    return

  afterEach ->
    sandbox.restore()

  describe 'AuthController', ->
    $scope = null
    $timeout = null
    auth = null
    session = null

    beforeEach inject ($controller, $rootScope, _$timeout_, _session_) ->
      $scope = $rootScope.$new()
      $timeout = _$timeout_
      auth = $controller 'AuthController', {$scope}
      session = _session_
      session.login.reset()

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

        assert.calledWith mockFormHelpers.applyValidationErrors, form,
          {username: 'taken'},
          'registration error'

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
        assert.isNull $scope.model, 'the model is erased'
        assert.called mockFlash, 'a notification is flashed'

      it 'should not happen if the model is empty', ->
        $scope.model = undefined
        $scope.$digest()
        assert.notCalled $timeout

        $scope.model = {}
        $scope.$digest()
        assert.notCalled $timeout
