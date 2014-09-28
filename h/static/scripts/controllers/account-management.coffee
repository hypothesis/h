class AccountManagement
  @inject = ['$scope', '$filter', 'flash', 'session', 'identity', 'formHelpers']

  constructor: ($scope, $filter, flash, session, identity, formHelpers) ->
    persona_filter = $filter('persona')

    onSuccess = (form, response) ->
      # Fire flash messages.
      for type, msgs of response.flash
        flash(type, msgs)

      form.$setPristine()
      formModel = form.$name.slice(0, -4)
      $scope[formModel] = {} # Reset form fields.
      $scope.$broadcast 'formState', form.$name, 'success'  # Update status btn

    onDelete = (form, response) ->
      identity.logout()
      onSuccess(form, response)

    onError = (form, response) ->
      if response.status >= 400 and response.status < 500
        formHelpers.applyValidationErrors(form, response.data.errors)
      else
        if response.data.flash
          flash(type, msgs) for own type, msgs of response.data.flash
        else
          flash('error', 'Sorry, we were unable to perform your request')

      $scope.$broadcast 'formState', form.$name, ''  # Update status btn

    # Data for each of the forms
    $scope.editProfile = {}
    $scope.changePassword = {}
    $scope.deleteAccount = {}

    $scope.delete = (form) ->
      # If the password is correct, the account is deleted.
      # The extension is then removed from the page.
      # Confirmation of success is given.
      return unless form.$valid
      username = persona_filter $scope.persona
      packet =
        username: username
        pwd: form.pwd.$modelValue

      successHandler = angular.bind(null, onDelete, form)
      errorHandler   = angular.bind(null, onError, form)

      promise = session.disable_user(packet)
      promise.$promise.then(successHandler, errorHandler)

    $scope.submit = (form) ->
      # In the frontend change_email and change_password are two different
      # forms. However, in the backend it is just one: edit_profile
      return unless form.$valid

      username = persona_filter $scope.persona
      packet =
        username: username
        pwd: form.pwd.$modelValue
        password: form.password.$modelValue

      successHandler = angular.bind(null, onSuccess, form)
      errorHandler   = angular.bind(null, onError, form)

      $scope.$broadcast 'formState', form.$name, 'loading'  # Update status btn
      promise = session.edit_profile(packet)
      promise.$promise.then(successHandler, errorHandler)


angular.module('h.controllers.AccountManagement', [])
.controller('AccountManagement', AccountManagement)
