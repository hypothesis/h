{module, inject} = require('angular-mock')

assert = chai.assert

VISIBILITY_KEY ='hypothesis.visibility'
VISIBILITY_PUBLIC = 'public'
VISIBILITY_PRIVATE = 'private'

describe 'h.directives.privacy', ->
  $compile = null
  $scope = null
  $window = null
  fakeAuth = null
  fakePermissions = null
  fakeLocalStorage = null
  sandbox = null

  before ->
    angular.module('h', [])
    require('../privacy')

  beforeEach module('h')
  beforeEach module('h.templates')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()

    fakeAuth = {
      user: 'acct:angry.joe@texas.com'
    }

    storage = {}
    fakeLocalStorage = {
      getItem: sandbox.spy (key) -> storage[key]
      setItem: sandbox.spy (key, value) -> storage[key] = value
      removeItem: sandbox.spy (key) -> delete storage[key]
    }

    fakePermissions = {
      isPublic: sandbox.stub().returns(true)
      isPrivate: sandbox.stub().returns(false)
      permits: sandbox.stub().returns(true)
      public: sandbox.stub().returns({read: ['everybody']})
      private: sandbox.stub().returns({read: ['justme']})
    }

    $provide.value 'auth', fakeAuth
    $provide.value 'localstorage', fakeLocalStorage
    $provide.value 'permissions', fakePermissions
    return

  beforeEach inject (_$compile_, _$rootScope_, _$window_) ->
    $compile = _$compile_
    $scope = _$rootScope_.$new()
    $window = _$window_

  afterEach ->
    sandbox.restore()

  describe 'saves visibility level', ->

    it 'stores the default visibility level when it changes', ->
      $scope.permissions = {read: ['acct:user@example.com']}
      $element = $compile('<privacy ng-model="permissions">')($scope)
      $scope.$digest()
      $isolateScope = $element.isolateScope()
      $isolateScope.setLevel(name: VISIBILITY_PUBLIC)

      expected = VISIBILITY_PUBLIC
      stored = fakeLocalStorage.getItem VISIBILITY_KEY
      assert.equal stored, expected

    describe 'setting permissions', ->
      $element = null

      describe 'when no setting is stored', ->
        beforeEach ->
          fakeLocalStorage.removeItem VISIBILITY_KEY

        it 'defaults to public', ->
          $scope.permissions = {read: []}
          $element = $compile('<privacy ng-model="permissions">')($scope)
          $scope.$digest()
          $isolateScope = $element.isolateScope()
          assert.equal $isolateScope.level.name, VISIBILITY_PUBLIC

      describe 'when permissions.read is empty', ->
        beforeEach ->
          fakeLocalStorage.setItem VISIBILITY_KEY, VISIBILITY_PUBLIC

          $scope.permissions = {read: []}
          $element = $compile('<privacy ng-model="permissions">')($scope)
          $scope.$digest()

        it 'sets the initial permissions based on the stored privacy level', ->
          assert.equal $element.isolateScope().level.name, VISIBILITY_PUBLIC

        it 'does not alter the level on subsequent renderings', ->
          fakeLocalStorage.setItem VISIBILITY_KEY, VISIBILITY_PRIVATE
          $scope.permissions.read = ['acct:user@example.com']
          $scope.$digest()
          assert.equal $element.isolateScope().level.name, VISIBILITY_PUBLIC

      describe 'when permissions.read is filled', ->
        it 'does not alter the level', ->
          fakeLocalStorage.setItem VISIBILITY_KEY, VISIBILITY_PRIVATE

          $scope.permissions = {read: ['group:__world__']}
          $element = $compile('<privacy ng-model="permissions">')($scope)
          $scope.$digest()
          $isolateScope = $element.isolateScope()
          assert.equal($isolateScope.level.name, VISIBILITY_PUBLIC)

      describe 'user attribute', ->
        beforeEach ->
          $scope.permissions = {read: []}

        it 'fills the permissions fields with the auth.user name', ->
          fakeLocalStorage.setItem VISIBILITY_KEY, VISIBILITY_PRIVATE
          $element = $compile('<privacy ng-model="permissions">')($scope)
          $scope.$digest()

          assert.deepEqual $scope.permissions, fakePermissions.private()

        it 'puts group_world into the read permissions for public visibility', ->
          fakeLocalStorage.setItem VISIBILITY_KEY, VISIBILITY_PUBLIC
          $element = $compile('<privacy ng-model="permissions">')($scope)
          $scope.$digest()

          assert.deepEqual $scope.permissions, fakePermissions.public()
