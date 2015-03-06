{inject, module} = require('angular-mock')

assert = chai.assert
sinon.assert.expose assert, prefix: null


describe 'h:AccountController', ->
  $scope = null
  fakeFlash = null
  fakeSession = null
  fakeIdentity = null
  fakeFormHelpers = null
  fakeAuth = null
  editProfilePromise = null
  disableUserPromise = null
  profilePromise = null
  createController = null
  sandbox = null

  before ->
    angular.module('h', [])
    require('../account-controller')

  beforeEach module('h')

  beforeEach module ($provide, $filterProvider) ->
    sandbox = sinon.sandbox.create()
    fakeSession = {}
    fakeFlash = sandbox.spy()
    fakeIdentity =
      logout: sandbox.spy()
    fakeFormHelpers =
      applyValidationErrors: sandbox.spy()
    fakeAuth =
      user: 'egon@columbia.edu'

    $filterProvider.register 'persona', ->
      sandbox.stub().returns('STUBBED_PERSONA_FILTER')

    $provide.value 'session', fakeSession
    $provide.value 'flash', fakeFlash
    $provide.value 'identity', fakeIdentity
    $provide.value 'formHelpers', fakeFormHelpers
    $provide.value 'auth', fakeAuth
    return

  beforeEach inject ($rootScope, $q, $controller) ->
    $scope = $rootScope.$new()

    disableUserPromise = {then: sandbox.stub()}
    editProfilePromise = {then: sandbox.stub()}
    profilePromise = {then: sandbox.stub()}
    fakeSession.edit_profile = sandbox.stub().returns($promise: editProfilePromise)
    fakeSession.disable_user = sandbox.stub().returns($promise: disableUserPromise)
    fakeSession.profile = sandbox.stub().returns($promise: profilePromise)

    createController = ->
      $controller('AccountController', {$scope: $scope})

  afterEach ->
    sandbox.restore()

  describe '.submit', ->
    createFakeForm = (overrides={}) ->
      defaults =
        $name: 'changePasswordForm'
        $valid: true
        $setPristine: sandbox.spy()
        pwd: $modelValue: 'gozer'
        password: $modelValue: 'paranormal'
      angular.extend(defaults, overrides)

    it 'updates the password on the backend', ->
      fakeForm = createFakeForm()
      controller = createController()
      $scope.submit(fakeForm)

      assert.calledWith(fakeSession.edit_profile, {
        username: 'STUBBED_PERSONA_FILTER'
        pwd: 'gozer'
        password: 'paranormal'
      })

    it 'clears the fields', ->
      controller = createController()
      $scope.changePassword = {pwd: 'password', password: 'password'}
      fakeForm = createFakeForm()

      # Resolve the request.
      editProfilePromise.then.yields(flash: {
        success: ['Your profile has been updated.']
      })
      $scope.submit(fakeForm)

      assert.deepEqual($scope.changePassword, {})

    it 'updates the error fields on bad response', ->
      fakeForm = createFakeForm()
      controller = createController()
      $scope.submit(fakeForm)

      # Resolve the request.
      editProfilePromise.then.callArg 1,
        status: 400
        data:
          errors:
            pwd: 'this is wrong'

      assert.calledWith fakeFormHelpers.applyValidationErrors, fakeForm,
        pwd: 'this is wrong'

    it 'displays a flash message on success', ->
      fakeForm = createFakeForm()

      # Resolve the request.
      editProfilePromise.then.yields(flash: {
        success: ['Your profile has been updated.']
      })

      controller = createController()
      $scope.submit(fakeForm)

      assert.calledWith(fakeFlash, 'success', [
        'Your profile has been updated.'
      ])

    it 'displays a flash message if a server error occurs', ->
      fakeForm = createFakeForm()
      controller = createController()
      $scope.submit(fakeForm)

      # Resolve the request.
      editProfilePromise.then.callArg 1,
        status: 500
        data:
          flash:
            error: ['Something bad happened']

      assert.calledWith(fakeFlash, 'error', ['Something bad happened'])

    it 'displays a fallback flash message if none are present', ->
      fakeForm = createFakeForm()
      controller = createController()
      $scope.submit(fakeForm)

      # Resolve the request.
      editProfilePromise.then.callArg 1,
        status: 500
        data: {}

      assert.calledWith(fakeFlash, 'error', 'Sorry, we were unable to perform your request')

  describe '.delete', ->
    createFakeForm = (overrides={}) ->
      defaults =
        $name: 'deleteAccountForm'
        $valid: true
        $setPristine: sandbox.spy()
        pwd: $modelValue: 'paranormal'
      angular.extend(defaults, overrides)

    it 'disables the user account', ->
      fakeForm = createFakeForm()
      controller = createController()
      $scope.delete(fakeForm)

      assert.calledWith fakeSession.disable_user,
        username: 'STUBBED_PERSONA_FILTER'
        pwd: 'paranormal'

    it 'logs the user out of the application', ->
      fakeForm = createFakeForm()
      controller = createController()
      $scope.delete(fakeForm)

      # Resolve the request.
      disableUserPromise.then.callArg 0,
        status: 200

      assert.calledWith(fakeIdentity.logout)

    it 'clears the password field', ->
      controller = createController()

      fakeForm = createFakeForm()
      $scope.deleteAccount = {pwd: ''}
      $scope.delete(fakeForm)
      disableUserPromise.then.callArg 0,
        status: 200

      assert.deepEqual($scope.deleteAccount, {})

    it 'updates the error fields on bad response', ->
      fakeForm = createFakeForm()
      controller = createController()
      $scope.delete(fakeForm)

      # Resolve the request.
      disableUserPromise.then.callArg 1,
        status: 400
        data:
          errors:
            pwd: 'this is wrong'

      assert.calledWith fakeFormHelpers.applyValidationErrors, fakeForm,
        pwd: 'this is wrong'

    it 'displays a flash message if a server error occurs', ->
      fakeForm = createFakeForm()
      controller = createController()
      $scope.delete(fakeForm)

      # Resolve the request.
      disableUserPromise.then.callArg 1,
        status: 500
        data:
          flash:
            error: ['Something bad happened']

      assert.calledWith(fakeFlash, 'error', ['Something bad happened'])

    it 'displays a fallback flash message if none are present', ->
      fakeForm = createFakeForm()
      controller = createController()
      $scope.delete(fakeForm)

      # Resolve the request.
      disableUserPromise.then.callArg 1,
        status: 500
        data: {}

      assert.calledWith(fakeFlash, 'error', 'Sorry, we were unable to perform your request')
