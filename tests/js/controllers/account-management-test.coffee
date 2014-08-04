assert = chai.assert
sinon.assert.expose assert, prefix: null
sandbox = sinon.sandbox.create()

describe 'h.controllers.AccountManagement', ->
  $scope = null
  fakeUtil = null
  fakeFlash = null
  fakeProfile = null
  editProfilePromise = null
  disableUserPromise = null
  createController = null

  beforeEach module ($provide) ->
    fakeProfile = {}
    fakeFlash = sandbox.spy()
    fakeUtil =
      applyValidationErrors: sandbox.spy()

    $provide.value '$filter', ->
      sandbox.stub().returns('STUBBED_PERSONA_FILTER')

    $provide.value 'profile', fakeProfile
    $provide.value 'flash', fakeFlash
    $provide.value 'util', fakeUtil
    return

  beforeEach module('h.controllers')

  beforeEach inject ($rootScope, $q, $controller) ->
    $scope = $rootScope.$new()
    $scope.session = persona: 'egon@columbia.edu'

    disableUserPromise = {then: sandbox.stub()}
    editProfilePromise = {then: sandbox.stub()}
    fakeProfile.edit_profile = sandbox.stub().returns($promise: editProfilePromise)
    fakeProfile.disable_user = sandbox.stub().returns($promise: disableUserPromise)

    createController = ->
      $controller('AccountManagement', {$scope: $scope})

  describe '.submit', ->
    it 'updates the email address on the backend', ->
      fakeForm =
        $name: 'editProfile'
        $valid: true
        email: $modelValue: 'egon@columbia.edu'
        password: $modelValue: 'paranormal'

      controller = createController()
      $scope.submit(fakeForm)

      assert.calledWith(fakeProfile.edit_profile, {
        username: 'STUBBED_PERSONA_FILTER'
        email: 'egon@columbia.edu'
        pwd: 'paranormal'
      })

    it 'updates the password on the backend', ->
      fakeForm =
        $name: 'changePassword'
        $valid: true
        oldpassword: $modelValue: 'gozer'
        newpassword: $modelValue: 'paranormal'

      controller = createController()
      $scope.submit(fakeForm)

      assert.calledWith(fakeProfile.edit_profile, {
        username: 'STUBBED_PERSONA_FILTER'
        pwd: 'gozer'
        password: 'paranormal'
      })

    it 'displays a flash message on success', ->
      fakeForm =
        $name: 'changePassword'
        $valid: true
        oldpassword: $modelValue: 'gozer'
        newpassword: $modelValue: 'paranormal'

      # Resolve the request.
      editProfilePromise.then.yields(flash: {
        success: ['Your profile has been updated.']
      })

      controller = createController()
      $scope.submit(fakeForm)

      assert.calledWith(fakeFlash, 'success', [
        'Your profile has been updated.'
      ])

    it 'updates the error fields on bad response', ->
      fakeForm =
        $name: 'changePassword'
        $valid: true
        oldpassword: $modelValue: 'gozer'
        newpassword: $modelValue: 'paranormal'

      controller = createController()
      $scope.submit(fakeForm)

      # Resolve the request.
      editProfilePromise.then.callArg 1,
        status: 400
        errors:
          oldpassword: 'this is wrong'


      assert.calledWith fakeUtil.applyValidationErrors, fakeForm,
        oldpassword: 'this is wrong'

    it 'displays a flash message if a server error occurs', ->
      fakeForm =
        $name: 'changePassword'
        $valid: true
        oldpassword: $modelValue: 'gozer'
        newpassword: $modelValue: 'paranormal'

      controller = createController()
      $scope.submit(fakeForm)

      # Resolve the request.
      editProfilePromise.then.callArg 1,
        status: 500

      assert.calledWith(fakeFlash, 'error')

  describe '.deleteAccount', ->
    it 'disables the user account', ->
      fakeForm =
        $name: 'deleteAccount'
        $valid: true
        deleteaccountpassword: $modelValue: 'paranormal'

      controller = createController()
      $scope.deleteAccount(fakeForm)

      assert.calledWith fakeProfile.disable_user,
        username: 'STUBBED_PERSONA_FILTER'
        pwd: 'paranormal'

    it 'logs the user out of the application'

    it 'updates the error fields on bad response', ->
      fakeForm =
        $name: 'deleteAccount'
        $valid: true
        deleteaccountpassword: $modelValue: 'paranormal'

      controller = createController()
      $scope.deleteAccount(fakeForm)

      # Resolve the request.
      disableUserPromise.then.callArg 1,
        status: 400
        errors:
          oldpassword: 'this is wrong'

      assert.calledWith fakeUtil.applyValidationErrors, fakeForm,
        oldpassword: 'this is wrong'

    it 'displays a flash message if a server error ocurrs', ->
      fakeForm =
        $name: 'deleteAccount'
        $valid: true
        deleteaccountpassword: $modelValue: 'paranormal'

      controller = createController()
      $scope.deleteAccount(fakeForm)

      # Resolve the request.
      disableUserPromise.then.callArg 1,
        status: 500

      assert.calledWith(fakeFlash, 'error')

