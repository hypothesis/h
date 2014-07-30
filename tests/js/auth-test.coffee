assert = chai.assert
sinon.assert.expose assert, prefix: null
sandbox = sinon.sandbox.create()


class MockSession
  $login: sandbox.stub()
  $register: (callback, errback) ->
    errback
      data:
        errors:
          username: 'taken'
        reason: 'registration error'

mockUtil = applyValidationErrors: sandbox.spy()

describe 'h.auth', ->
  beforeEach module('h.auth')

  beforeEach module ($provide) ->
    $provide.value '$timeout', sandbox.spy()
    $provide.value 'flash', sandbox.spy()
    $provide.value 'session', new MockSession()
    $provide.value 'util', mockUtil
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
      session.$login.reset()

    describe '#submit()', ->
      it 'should call session methods on submit', ->
        auth.submit
          $name: 'login'
          $valid: true

        assert.called session.$login

      it 'should do nothing when the form is invalid', ->
        auth.submit
          $name: 'login'
          $valid: false

        assert.notCalled session.$login

      it 'should set response errors', ->
        form =
          $name: 'register'
          $valid: true
          username:
            $setValidity: sandbox.stub()
          email:
            $setValidity: sandbox.stub()

        auth.submit(form)

        assert.calledWith mockUtil.applyValidationErrors, form,
          username: 'taken'
        assert.equal form.responseErrorMessage, 'registration error'

    describe 'timeout', ->
      it 'should happen after a period of inactivity', ->
        sandbox.spy $scope, '$broadcast'
        $scope.model =
          username: 'test'
          email: 'test@example.com'
          password: 'secret'
          code: '1234'

        $scope.$digest()
        assert.called $timeout

        $timeout.lastCall.args[0]()
        assert.isNull $scope.model, 'the model is erased'

        assert.calledWith $scope.$broadcast, 'timeout'

      it 'should not happen if the model is empty', ->
        $scope.$digest()
        assert.notCalled $timeout


  describe 'authDirective', ->
    elem = null
    session = null
    $rootScope = null
    $scope = null

    beforeEach inject ($compile, _$rootScope_, _session_) ->
      elem = angular.element(
        '''
        <div class="auth" ng-form="form"
             on-error="stub" on-success="stub" on-timeout="stub">
          <form name="login">
            <input type="text" name="username" ng-model="username"></input>
          </form>
        </div>
        '''
      )
      session = _session_
      $rootScope = _$rootScope_
      $scope = $compile(elem)($rootScope).scope()
      $scope.$digest()

    it 'should reset response errors before submit', ->
      $scope.form.login.responseErrorMessage = 'test'
      $scope.form.login.username.$setValidity('response', false)
      assert.isFalse $scope.form.login.$valid

      elem.find('input').trigger('submit')
      assert.isTrue $scope.form.login.$valid
      assert.isNull $scope.form.login.responseErrorMessage

    it 'should reset to pristine state when the model is reset', ->
      $scope.form.$setDirty()
      $scope.$digest()
      assert.isFalse $scope.form.$pristine

      $scope.model = null
      $scope.$digest()
      assert.isTrue $scope.form.$pristine

    it 'should invoke handlers set by attributes', ->
      $scope.stub = sandbox.stub()
      for event in ['error', 'success', 'timeout']
        $scope.stub.reset()
        $scope.$broadcast(event)
        assert.called $scope.stub
