imports = [
  'h.session'
]


class AuthController
  this.$inject = ['$scope', '$timeout', 'session']
  constructor:   ( $scope,   $timeout,   session ) ->
    timeout = null

    this.submit = (form) ->
      return unless form.$valid

      data = {}
      method = '$' + form.$name

      for own key of session
        delete session[key]

      angular.extend session, $scope.model

      session[method](
        (session) ->
          $scope.model = null
          $scope.$broadcast 'success'
      , (response) ->
          {errors, reason} = response.data

          if reason
            if reason == 'Invalid username or password.'
              form.password.$setValidity('response', false)
              form.password.responseErrorMessage = reason
            else
              form.responseErrorMessage = reason
          else
            form.responseErrorMessage = null

          for field, error of errors
            form[field].$setValidity('response', false)
            form[field].responseErrorMessage = error

          $scope.$broadcast 'error', form.$name
      )

    $scope.$on '$destroy', ->
      if timeout
        $timeout.cancel timeout

    $scope.$watchCollection 'model', (value) ->
      # Reset the auth forms after five minutes of inactivity
      if timeout
        $timeout.cancel timeout

      # If the model is not empty, start the timeout
      if value
        timeout = $timeout ->
          $scope.model = null
          $scope.$broadcast 'timeout'
        , 300000


authDirective = ->
  controller: 'AuthController'
  link: (scope, elem, attrs, [form, auth]) ->
    elem.on 'submit', (event) ->
      scope.$apply ->
        $target = angular.element event.target
        $form = $target.controller('form')

        $form.responseErrorMessage = null

        for ctrl in $form.$error.response?.slice?() or []
          ctrl.$setValidity('response', true)

        auth.submit($form)

    scope.$on 'error', (event) ->
      scope[attrs.onError]?(event)

    scope.$on 'success', (event) ->
      scope[attrs.onSuccess]?(event)

    scope.$on 'timeout', (event) ->
      scope[attrs.onTimeout]?(event)

    scope.$watch 'model', (value) ->
      if value is null
        form.$setPristine()
  require: ['form', 'auth']
  restrict: 'C'
  scope: true


angular.module('h.auth', imports)
.controller('AuthController', AuthController)
.directive('auth', authDirective)
