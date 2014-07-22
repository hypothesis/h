assert = chai.assert
sinon.assert.expose assert, prefix: null

describe 'h.auth', ->
  beforeEach module('h.auth')

  beforeEach module ($provide) ->
    $provide.value 'flash', sinon.spy()
    $provide.factory 'session', ($q, $rootScope) ->
    return

  describe 'AuthController', ->
    $q = null
    $scope = null
    $timeout = null
    auth = null

    beforeEach inject ($controller, _$q_, $rootScope, _$timeout_) ->
      $q = _$q_
      $scope = $rootScope.$new()
      $scope.model = {}
      $timeout = _$timeout_
      auth = $controller 'AuthController', {$scope}

    describe '#submit()', ->
      it 'should call model handler methods on submit', ->
        $scope.model.foo = 'bar'
        $scope.model.$login = sinon.spy ->
          this.foo = 'baz'
          dfd = $q.defer()
          dfd.resolve()
          $scope.$apply()
          dfd.promise

        auth.submit
          $valid: true
          $name: 'login'

        assert.called $scope.model.$login
        assert.equal $scope.model.foo, 'baz'

      it 'should do nothing when the form is invalid', ->
        $scope.model.$login = sinon.spy()

        auth.submit
          $name: 'login'
          $valid: false

        assert.notCalled $scope.model.$login

    describe '#reset()', ->
      beforeEach ->
        sinon.spy auth, 'reset'

      it 'should happen after a timeout', ->
        base =
          username: 'test'
          email: 'test@example.com'
          password: 'secret'
          code: '1234'

        angular.extend $scope.model, base
        $scope.$digest()
        $timeout.flush()

        assert.calledOnce auth.reset
        for key of base
          assert.isNull $scope.model[key]

      it 'should not happen if the model is empty', ->
        $scope.$digest()
        $timeout.flush()
        assert.notCalled auth.reset
