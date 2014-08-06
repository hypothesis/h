assert = chai.assert
sinon.assert.expose assert, prefix: null
sandbox = sinon.sandbox.create()

describe 'h.controllers.AccountManagement', ->
  $scope = null
  fakeUtil = null
  fakeFlash = null
  fakeProfile = null
  fakeIdentity = null
  editProfilePromise = null
  disableUserPromise = null
  createController = null

  beforeEach module ($provide, $filterProvider) ->
    fakeProfile = {}
    fakeFlash = sandbox.spy()
    fakeIdentity =
      logout: sandbox.spy()
    fakeUtil =
      applyValidationErrors: sandbox.spy()

    $filterProvider.register 'persona', ->
      sandbox.stub().returns('STUBBED_PERSONA_FILTER')

    $provide.value 'profile', fakeProfile
    $provide.value 'flash', fakeFlash
    $provide.value 'identity', fakeIdentity
    $provide.value 'util', fakeUtil
    return

  beforeEach module('h.controllers.AccountManagement')

  beforeEach inject ($rootScope, $q, $controller) ->
    $scope = $rootScope.$new()
    $scope.session = userid: 'egon@columbia.edu'

    disableUserPromise = {then: sandbox.stub()}
    editProfilePromise = {then: sandbox.stub()}
    fakeProfile.edit_profile = sandbox.stub().returns($promise: editProfilePromise)
    fakeProfile.disable_user = sandbox.stub().returns($promise: disableUserPromise)

    createController = ->
      $controller('AccountManagement', {$scope: $scope})

  describe '.submit', ->
    it 'updates the email address on the backend', ->
      fakeForm =
        $name: 'editProfileForm'
        $valid: true
        $setPristine: sandbox.spy()
        email: $modelValue: 'egon@columbia.edu'
        pwd: $modelValue: 'paranormal'

      controller = createController()
      $scope.submit(fakeForm)

      assert.calledWith(fakeProfile.edit_profile, {
        username: 'STUBBED_PERSONA_FILTER'
        email: 'egon@columbia.edu'
        pwd: 'paranormal'
      })

    it 'updates the password on the backend', ->
      fakeForm =
        $name: 'changePasswordForm'
        $valid: true
        $setPristine: sandbox.spy()
        pwd: $modelValue: 'gozer'
        password: $modelValue: 'paranormal'

      controller = createController()
      $scope.submit(fakeForm)

      assert.calledWith(fakeProfile.edit_profile, {
        username: 'STUBBED_PERSONA_FILTER'
        pwd: 'gozer'
        password: 'paranormal'
      })

    it 'displays a flash message on success', ->
      fakeForm =
        $name: 'changePasswordForm'
        $valid: true
        $setPristine: sandbox.spy()
        pwd: $modelValue: 'gozer'
        password: $modelValue: 'paranormal'

      # Resolve the request.
      editProfilePromise.then.yields(flash: {
        success: ['Your profile has been updated.']
      })

      controller = createController()
      $scope.submit(fakeForm)

      assert.calledWith(fakeFlash, 'success', [
        'Your profile has been updated.'
      ])

    it 'clears the password field', ->
      controller = createController()

      $scope.changePassword = {pwd: 'password', password: 'password'}

      fakeForm =
        $name: 'changePasswordForm'
        $valid: true
        $setPristine: sandbox.spy()
        pwd: $modelValue: 'gozer'
        password: $modelValue: 'paranormal'

      # Resolve the request.
      editProfilePromise.then.yields(flash: {
        success: ['Your profile has been updated.']
      })
      $scope.submit(fakeForm)

      assert.deepEqual($scope.changePassword, {})

    it 'updates the error fields on bad response', ->
      fakeForm =
        $name: 'changePasswordForm'
        $valid: true
        $setPristine: sandbox.spy()
        pwd: $modelValue: 'gozer'
        password: $modelValue: 'paranormal'

      controller = createController()
      $scope.submit(fakeForm)

      # Resolve the request.
      editProfilePromise.then.callArg 1,
        status: 400
        errors:
          pwd: 'this is wrong'

      assert.calledWith fakeUtil.applyValidationErrors, fakeForm,
        pwd: 'this is wrong'

    it 'displays a flash message if a server error occurs', ->
      fakeForm =
        $name: 'changePasswordForm'
        $valid: true
        $setPristine: sandbox.spy()
        pwd: $modelValue: 'gozer'
        password: $modelValue: 'paranormal'

      controller = createController()
      $scope.submit(fakeForm)

      # Resolve the request.
      editProfilePromise.then.callArg 1,
        status: 500

      assert.calledWith(fakeFlash, 'error')

  describe '.delete', ->
    it 'disables the user account', ->
      fakeForm =
        $name: 'deleteAccountForm'
        $valid: true
        $setPristine: sandbox.spy()
        pwd: $modelValue: 'paranormal'

      controller = createController()
      $scope.delete(fakeForm)

      assert.calledWith fakeProfile.disable_user,
        username: 'STUBBED_PERSONA_FILTER'
        pwd: 'paranormal'

    it 'logs the user out of the application', ->
      fakeForm =
        $name: 'deleteAccountForm'
        $valid: true
        $setPristine: sandbox.spy()
        pwd: $modelValue: 'paranormal'

      controller = createController()
      $scope.delete(fakeForm)

      # Resolve the request.
      disableUserPromise.then.callArg 0,
        status: 200

      assert.calledWith(fakeIdentity.logout)

    it 'clears the password field', ->
      controller = createController()

      fakeForm =
        $name: 'deleteAccountForm'
        $valid: true
        $setPristine: sandbox.spy()
        pwd: $modelValue: 'paranormal'

      $scope.deleteAccount = {pwd: ''}
      $scope.delete(fakeForm)
      disableUserPromise.then.callArg 0,
        status: 200

      assert.deepEqual($scope.deleteAccount, {})

    it 'updates the error fields on bad response', ->
      fakeForm =
        $name: 'deleteAccountForm'
        $valid: true
        $setPristine: sandbox.spy()
        pwd: $modelValue: 'paranormal'

      controller = createController()
      $scope.delete(fakeForm)

      # Resolve the request.
      disableUserPromise.then.callArg 1,
        status: 400
        errors:
          pwd: 'this is wrong'

      assert.calledWith fakeUtil.applyValidationErrors, fakeForm,
        pwd: 'this is wrong'

    it 'displays a flash message if a server error ocurrs', ->
      fakeForm =
        $name: 'deleteAccountForm'
        $valid: true
        $setPristine: sandbox.spy()
        pwd: $modelValue: 'paranormal'

      controller = createController()
      $scope.delete(fakeForm)

      # Resolve the request.
      disableUserPromise.then.callArg 1,
        status: 500

      assert.calledWith(fakeFlash, 'error')

