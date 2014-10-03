class AuthController
  this.$inject = ['$scope', '$timeout', 'flash', 'session', 'formHelpers']
  constructor:   ( $scope,   $timeout,   flash,   session,   formHelpers ) ->
    timeout = null

    success = (data) ->
      if $scope.tab is 'forgot' then $scope.tab = 'activate'
      if data.userid then $scope.$emit 'auth', null, data
      $scope.model = null
      $scope.form?.$setPristine()

    failure = (form, response) ->
      {errors, reason} = response.data
      formHelpers.applyValidationErrors(form, errors, reason)

    this.submit = (form) ->
      delete form.responseErrorMessage
      form.$setValidity('response', true)

      return unless form.$valid

      $scope.$broadcast 'formState', form.$name, 'loading'
      session[form.$name] $scope.model, success,
        angular.bind(this, failure, form)
      .$promise.finally -> $scope.$broadcast 'formState', form.$name, ''

    $scope.model = null
    $scope.tab = 'login'

    $scope.$on 'auth', do ->
      preventCancel = $scope.$on '$destroy', ->
        if timeout then $timeout.cancel timeout
        $scope.$emit 'auth', 'cancel'

    $scope.$watchCollection 'model', (value) ->
      # Reset the auth forms after five minutes of inactivity
      if timeout
        $timeout.cancel timeout

      # If the model is not empty, start the timeout
      if value and not angular.equals(value, {})
        timeout = $timeout ->
          $scope.form?.$setPristine()
          $scope.model = null
          flash 'info',
            'For your security, the forms have been reset due to inactivity.'
        , 300000



angular.module('h.auth')
.controller('AuthController', AuthController)
