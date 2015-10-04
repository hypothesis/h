{inject, module} = angular.mock

describe 'h:AccountController', ->
  $scope = null
  fakeFlash = null
  fakeSession = null
  fakeIdentity = null
  fakeFormRespond = null
  fakeAuth = null
  editProfilePromise = null
  disableUserPromise = null
  profilePromise = null
  createController = null
  sandbox = null

  before ->
    angular.module('h', [])
    .controller('AccountController', require('../account-controller'))

  beforeEach module('h')

  beforeEach module ($provide, $filterProvider) ->
    sandbox = sinon.sandbox.create()
    fakeSession = {}
    fakeFlash =
      success: sandbox.spy()
      info: sandbox.spy()
      warning: sandbox.spy()
      error: sandbox.spy()
    fakeIdentity =
      logout: sandbox.spy()
    fakeFormRespond = sandbox.spy()
    fakeAuth =
      user: 'egon@columbia.edu'

    $filterProvider.register 'persona', ->
      sandbox.stub().returns('STUBBED_PERSONA_FILTER')

    $provide.value 'session', fakeSession
    $provide.value 'flash', fakeFlash
    $provide.value 'identity', fakeIdentity
    $provide.value 'formRespond', fakeFormRespond
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

      assert.calledWith fakeFormRespond, fakeForm,
        pwd: 'this is wrong'

    it 'displays a flash message on success', ->
      fakeForm = createFakeForm()

      # Resolve the request.
      editProfilePromise.then.yields(flash: {
        success: ['Your profile has been updated.']
      })

      controller = createController()
      $scope.submit(fakeForm)

      assert.calledWith(fakeFlash.success, 'Your profile has been updated.')

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

      assert.calledWith(fakeFlash.error, 'Something bad happened')

    it 'displays a fallback flash message if none are present', ->
      fakeForm = createFakeForm()
      controller = createController()
      $scope.submit(fakeForm)

      # Resolve the request.
      editProfilePromise.then.callArg 1,
        status: 500
        data: {}

      assert.calledWith(fakeFlash.error,
        'Sorry, we were unable to perform your request')

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

      assert.calledWith fakeFormRespond, fakeForm,
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

      assert.calledWith(fakeFlash.error, 'Something bad happened')

    it 'displays a fallback toast message if none are present', ->
      fakeForm = createFakeForm()
      controller = createController()
      $scope.delete(fakeForm)

      # Resolve the request.
      disableUserPromise.then.callArg 1,
        status: 500
        data: {}

      assert.calledWith(fakeFlash.error,
        'Sorry, we were unable to perform your request')

describe "h:AccountController", ->

  before(->
    try
      # If this runs without error then the h module has already been defined
      # by an earlier top-level describe() in this file.
      angular.module("h")
    catch error
      # The h module hasn't been defined yet, so we need to define it
      # (this happens when it.only() is used in this describe()).
      angular.module("h", [])
      .controller('AccountController', require('../account-controller'))
  )

  beforeEach module('h')

  # Return the $controller service from Angular.
  getControllerService = ->
    $controller = null
    inject((_$controller_) ->
      $controller = _$controller_
    )
    return $controller

  # Return the $rootScope service from Angular.
  getRootScope = ->
    $rootScope = null
    inject((_$rootScope_) ->
      $rootScope = _$rootScope_
    )
    return $rootScope

  # Return a minimal stub version of h's session service.
  getStubSession = ({profile, edit_profile}) ->
    return {
      profile: -> profile or {$promise: Promise.resolve({})}
      edit_profile: edit_profile or -> {$promise: Promise.resolve({})}
    }

  # Return a minimal stub version of the object that AccountController's
  # changeEmailSubmit() method receives when the user submits the changeEmailForm.
  getStubChangeEmailForm = ({email, emailAgain, password}) ->
    return {
      $name: "changeEmailForm"
      email:
        $modelValue: email
        $setValidity: ->
      emailAgain:
        $modelValue: emailAgain
        $setValidity: ->
      pwd:
        $modelValue: password
        $setValidity: ->
      $valid: true
      $setPristine: ->
      $setValidity: ->
    }

  # Return an AccountController instance and stub services.
  createAccountController = ({$scope, $filter, auth, flash, formRespond,
                              identity, session}) ->
    locals = {
      $scope: $scope or getRootScope().$new()
      $filter: $filter or -> -> {}
      auth: auth or {}
      flash: flash or {}
      formRespond: formRespond or ->
      identity: identity or {}
      session: session or getStubSession({})
    }
    locals["ctrl"] = getControllerService()("AccountController", locals)
    return locals

  ###
  The controller sets $scope.email to the user's current email address on
  controller initialization. The templates use this for the placeholder
  value of the email input fields.
  ###
  it "adds the current email address to the scope when initialized", ->
    # The controller actually calls session.profile() on init which returns
    # a promise, and when that promise resolves it uses the value to set
    # $scope.email. So we need to stub that promise here.
    profilePromise = Promise.resolve({
      email: "test_user@test_email.com"
    })
    {$scope} = createAccountController(
      session: {profile: -> {$promise: profilePromise}})

    profilePromise.then(->
      assert $scope.email == "test_user@test_email.com"
    )

  describe "changeEmail", ->

    it "calls sesson.edit_profile() with the right data on form submission", ->

      new_email_addr = "new_email_address@test.com"

      # Stub the session.edit_profile() function.
      edit_profile = sinon.stub()
      edit_profile.returns({$promise: Promise.resolve({})})

      {$scope} = createAccountController(
        session: getStubSession(edit_profile: edit_profile)
        # Simulate a logged-in user with username "joeuser"
        $filter: -> -> "joeuser")

      form = getStubChangeEmailForm(
        email: new_email_addr, emailAgain: new_email_addr, password: "pass")

      $scope.changeEmailSubmit(form).then(->
        assert edit_profile.calledWithExactly({
          username: "joeuser"
          pwd: "pass"
          email: new_email_addr
          emailAgain: new_email_addr
        })
      )

    it "updates placeholder after successfully changing the email address", ->
      new_email_addr = "new_email_address@test.com"

      {$scope} = createAccountController(
        # AccountController expects session.edit_profile() to respond with the
        # newly saved email address.
        session: getStubSession(
            edit_profile: -> {
              $promise: Promise.resolve({email: new_email_addr})
            }
          )
      )

      form = getStubChangeEmailForm(
        email: new_email_addr, emailAgain: new_email_addr, password: "pass")

      $scope.changeEmailSubmit(form).then(->
        assert $scope.email == new_email_addr
      )

    it "shows an error if the emails don't match", ->
      server_response = {
        status: 400,
        statusText: "Bad Request"
        data:
          errors:
            emailAgain: "The emails must match."
      }

      {$scope} = createAccountController(
        formRespond: require("../form-respond")()
        session: getStubSession(
          edit_profile: -> {$promise: Promise.reject(server_response)}
        )
      )

      form = getStubChangeEmailForm(
        email: "my_new_email_address@yahoo.com"
        emailAgain: "a_different_email_address@bluebottle.com"
        pwd: "pass")

      $scope.changeEmailSubmit(form).then(->
        assert form.emailAgain.responseErrorMessage == "The emails must match."
      )

    it "broadcasts 'formState' 'changeEmailForm' 'loading' on submit", ->
      {$scope} = createAccountController({})

      $scope.$broadcast = sinon.stub()

      form = getStubChangeEmailForm(
        email: "new_email_address@test.com",
        emailAgain: "new_email_address@test.com", password: "pass")
      $scope.changeEmailSubmit(form)

      assert $scope.$broadcast.calledWithExactly(
        "formState", "changeEmailForm", "loading")

    it "broadcasts 'formState' 'changeEmailForm' 'success' on success", ->
      {$scope} = createAccountController({})

      $scope.$broadcast = sinon.stub()

      form = getStubChangeEmailForm(
        email: "new_email_address@test.com",
        emailAgain: "new_email_address@test.com", password: "pass")

      $scope.changeEmailSubmit(form).then(->
        assert $scope.$broadcast.calledWithExactly(
          "formState", "changeEmailForm", "success")
      )

    it "broadcasts 'formState' 'changeEmailForm' '' on error", ->
      {$scope} = createAccountController(
        flash: {error: ->}
        session: getStubSession(
          edit_profile: -> {$promise: Promise.reject({data: {}})}
        )
      )

      $scope.$broadcast = sinon.stub()

      form = getStubChangeEmailForm(
        email: "new_email_address@test.com",
        emailAgain: "new_email_address@test.com", password: "pass")

      $scope.changeEmailSubmit(form).then(->
        assert $scope.$broadcast.calledWithExactly(
          "formState", "changeEmailForm", "")
      )

    it "shows an error if the password is wrong", ->
      # Mock of the server response you get when you enter the wrong password.
      server_response = {
        data:
          errors:
            pwd: "Invalid password"
        status: 401
        statusText: "Unauthorized"
      }

      {$scope} = createAccountController(
        formRespond: require("../form-respond")()
        session: getStubSession(
          edit_profile: -> {$promise: Promise.reject(server_response)}
        )
      )

      form = getStubChangeEmailForm(
        email: "new_email_address@test.com",
        emailAgain: "new_email_address@test.com", password: "pass")

      $scope.changeEmailSubmit(form).then(->
        assert form.pwd.responseErrorMessage == "Invalid password"
      )
