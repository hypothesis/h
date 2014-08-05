class AccountManagement
  @inject = ['$scope', '$rootScope', '$filter', 'flash', 'profile', 'util']

  constructor: ($scope, $rootScope, $filter, flash, profile, util) ->
    persona_filter = $filter('persona')

    onSuccess = (response) ->
      # Fire flash messages.
      for type, msgs of response.flash
        flash(type, msgs)

    onError = (form, data) ->
      if 400 >= data.status < 500
        util.applyValidationErrors(form, data.errors)
      else
        flash('error', 'Sorry, we were unable to perform your request')

    $scope.deleteAccount = (form) ->
      # If the password is correct, the account is deleted.
      # The extension is then removed from the page.
      # Confirmation of success is given.
      return unless form.$valid
      username = persona_filter $scope.session.persona
      packet =
        username: username
        pwd: form.deleteaccountpassword.$modelValue

      promise = profile.disable_user(packet)
      promise.$promise.then(onSuccess, angular.bind(null, onError, form))

    $scope.submit = (form) ->
      # In the frontend change_email and change_password are two different
      # forms. However, in the backend it is just one: edit_profile
      return unless form.$valid

      username = persona_filter $scope.session.persona
      if form.$name is 'editProfile'
        packet =
          username: username
          email: form.email.$modelValue
          pwd: form.password.$modelValue
      else
        packet =
          username: username
          pwd: form.oldpassword.$modelValue
          password: form.newpassword.$modelValue

      promise = profile.edit_profile(packet)
      promise.$promise.then(onSuccess, angular.bind(null, onError, form))

    $rootScope.$on 'nav:account', ->
      $scope.sheet = true

    $rootScope.$on 'logout', ->
      $scope.sheet = false

angular.module('h.controllers.AccountManagement', [])
.controller('AccountManagement', AccountManagement)
