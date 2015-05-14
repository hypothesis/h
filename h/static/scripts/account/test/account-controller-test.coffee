{inject, module} = require('angular-mock')

assert = chai.assert
sinon.assert.expose assert, prefix: null


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
    require('../account-controller')

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
    require("../account-controller")
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

  ###
  Return an AccountController instance and stub services.

  Returns an object containing:

  * an AccountController instance with all the services it depends on
    stubbed, and
  * each of the stubbed services

  The returned object looks like this:

      {"ctrl": the AccountController instance
       "$scope": the scope attached to ctrl
       "$filter": the stub filter injected into ctrl
       "auth": the stub auth service injected into ctrl
       ... (more stubbed services here)
      }

   Use CoffeeScript's destructuring assignment to pull out just the things
   you need from the returned object. For example:

       {ctrl, $scope} = controller({})

   By default this does the minimum amount of stubbing necessary to create an
   AccountController without it crashing. For each of the services that gets
   stubbed the caller can optionally pass in their own object to be used
   instead of the minimal stub. For example:

       session = {profile: -> {$promise: ...}}
       {ctrl, $scope} = controller(session: session)
  ###
  controller = ({$scope, $filter, auth, flash, formRespond, identity,
                session}) ->
    locals = {
      $scope: $scope or getRootScope().$new()
      $filter: $filter or -> -> {}
      auth: auth or {}
      flash: flash or {}
      formRespond: formRespond or {}
      identity: identity or {}
      session: session or {profile: -> {$promise: Promise.resolve()}}
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
    session = {profile: -> {$promise: profilePromise}}
    {ctrl, $scope} = controller(session: session)

    profilePromise.then(->
      assert $scope.email == "test_user@test_email.com"
    )
