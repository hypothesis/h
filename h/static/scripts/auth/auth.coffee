imports = [
  'h.session'
]


class AuthController
  this.$inject = ['$scope', '$timeout', 'flash', 'session', 'formHelpers']
  constructor:   ( $scope,   $timeout,   flash,   session,   formHelpers ) ->
    timeout = null

    success = (data) ->
      $scope.tab = if $scope.tab is 'forgot' then 'activate' else null
      $scope.model = null
      $scope.$emit 'session', data

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

    $scope.$on '$destroy', ->
      if timeout
        $timeout.cancel timeout

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


angular.module('h.auth', imports)
.controller('AuthController', AuthController)
