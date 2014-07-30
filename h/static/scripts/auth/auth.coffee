imports = [
  'h.session'
]


class AuthController
  this.$inject = ['$scope', '$timeout', 'session', 'util']
  constructor:   ( $scope,   $timeout,   session,   util ) ->
    timeout = null

    success = ->
      $scope.tab = if $scope.tab is 'forgot' then 'activate' else null
      $scope.model = null
      $scope.$broadcast 'success'

    failure = (form, response) ->
      {errors, reason} = response.data

      if reason
        if reason == 'Invalid username or password.'
          form.password.$setValidity('response', false)
          form.password.responseErrorMessage = reason
        else
          form.responseErrorMessage = reason
      else
        form.responseErrorMessage = null

      util.applyValidationErrors(form, errors)

    this.submit = (form) ->
      return unless form.$valid

      data = {}
      method = '$' + form.$name

      angular.copy $scope.model, session
      session.$promise = session[method] success,
        angular.bind(this, failure, form)
      session.$resolved = false

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
          $scope.model = null
          $scope.$broadcast 'timeout'
        , 300000


authDirective = ['$timeout', ($timeout) ->
  controller: 'AuthController'
  link: (scope, elem, attrs, [auth, form]) ->
    elem.on 'submit', (event) ->
      scope.$apply ->
        $target = angular.element event.target
        $form = $target.controller('form')

        delete $form.responseErrorMessage

        for ctrl in $form.$error.response?.slice?() or []
          ctrl.$setValidity('response', true)

        auth.submit($form)

    scope.model = {}

    scope.$on 'authorize', ->
      scope.tab = 'login'

    scope.$on 'error', (event) ->
      scope.onError()

    scope.$on 'success', (event) ->
      scope.onSuccess()

    scope.$on 'timeout', (event) ->
      scope.onTimeout()

    scope.$watch 'model', (value) ->
      if value is null
        form.$setPristine()

    scope.$watch 'tab', (name) ->
      $timeout ->
        elem
          .find('form')
          .filter(-> this.name is name)
          .find('input')
          .filter(-> this.type isnt 'hidden')
          .first()
          .focus()
  require: ['auth', 'form']
  restrict: 'C'
  scope:
    onError: '&'
    onSuccess: '&'
    onTimeout: '&'
    session: '='
    tab: '=ngModel'
  templateUrl: 'auth.html'
]


angular.module('h.auth', imports)
.controller('AuthController', AuthController)
.directive('auth', authDirective)
