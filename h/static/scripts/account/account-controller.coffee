class AccountController
  @inject = [  '$scope', '$filter',
               'auth', 'flash', 'formRespond', 'identity', 'session']
  constructor: ($scope,   $filter,
                auth,   flash,   formRespond,   identity,   session) ->
    persona_filter = $filter('persona')
    $scope.subscriptionDescription =
      reply: 'Someone replies to one of my annotations'

    onSuccess = (form, response) ->
      # Fire flash messages.
      for type, msgs of response.flash
        for m in msgs
          flash[type](m)

      form.$setPristine()
      formModel = form.$name.slice(0, -4)
      $scope[formModel] = {} # Reset form fields.
      $scope.$broadcast 'formState', form.$name, 'success'  # Update status btn
      $scope.email = response.email

    onDelete = (form, response) ->
      identity.logout()
      onSuccess(form, response)

    onError = (form, response) ->
      if response.status >= 400 and response.status < 500
        formRespond(form, response.data.errors)
      else
        if response.data.flash
          for own type, msgs of response.data.flash
            for m in msgs
              flash[type](m)
        else
          flash.error('Sorry, we were unable to perform your request')

      $scope.$broadcast 'formState', form.$name, ''  # Update status btn

    $scope.tab = 'Account'
    session.profile().$promise
      .then (result) =>
        $scope.subscriptions = result.subscriptions
        $scope.email = result.email

    # Data for each of the forms
    $scope.editProfile = {}
    $scope.changePassword = {}
    $scope.deleteAccount = {}

    $scope.delete = (form) ->
      # If the password is correct, the account is deleted.
      # The extension is then removed from the page.
      # Confirmation of success is given.
      return unless form.$valid
      username = persona_filter auth.user
      packet =
        username: username
        pwd: form.pwd.$modelValue

      successHandler = angular.bind(null, onDelete, form)
      errorHandler   = angular.bind(null, onError, form)

      promise = session.disable_user(packet)
      promise.$promise.then(successHandler, errorHandler)

    $scope.submit = (form) ->
      formRespond(form)
      return unless form.$valid

      username = persona_filter auth.user
      packet =
        username: username
        pwd: form.pwd.$modelValue
        password: form.password.$modelValue

      successHandler = angular.bind(null, onSuccess, form)
      errorHandler   = angular.bind(null, onError, form)

      $scope.$broadcast 'formState', form.$name, 'loading'  # Update status btn
      promise = session.edit_profile(packet)
      promise.$promise.then(successHandler, errorHandler)

    $scope.changeEmail = (form) ->
      formRespond(form)
      return unless form.$valid

      username = persona_filter auth.user
      packet =
        username: username
        pwd: form.pwd.$modelValue
        email: form.email.$modelValue
        emailAgain: form.emailAgain.$modelValue

      successHandler = angular.bind(null, onSuccess, form)
      errorHandler   = angular.bind(null, onError, form)

      $scope.$broadcast 'formState', form.$name, 'loading'  # Update status btn
      promise = session.edit_profile(packet)
      promise.$promise.then(successHandler, errorHandler)

    $scope.updated = (index, form) ->
      packet =
        username: auth.user
        subscriptions: JSON.stringify $scope.subscriptions[index]

      successHandler = angular.bind(null, onSuccess, form)
      errorHandler   = angular.bind(null, onError, form)
      promise = session.edit_profile(packet)
      promise.$promise.then(successHandler, errorHandler)



angular.module('h')
.controller('AccountController', AccountController)
