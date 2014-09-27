imports = [
  'h.session'
]


class AuthController
  this.$inject = ['$scope', '$timeout', 'session', 'formHelpers']
  constructor:   ( $scope,   $timeout,   session,   formHelpers ) ->
    timeout = null

    success = ->
      $scope.tab = if $scope.tab is 'forgot' then 'activate' else null
      $scope.model = null
      $scope.$broadcast 'success'

    failure = (form, response) ->
      {errors, reason} = response.data
      formHelpers.applyValidationErrors(form, errors, reason)

    this.submit = (form) ->
      delete form.responseErrorMessage
      form.$setValidity('response', true)

      return unless form.$valid

      data = {}
      method = '$' + form.$name

      angular.copy $scope.model, session
      session.$promise = session[method] success,
        angular.bind(this, failure, form)
      session.$resolved = false

      # Update status btn
      $scope.$broadcast 'formState', form.$name, 'loading'
      session.$promise.finally ->
        $scope.$broadcast 'formState', form.$name, ''

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
        auth.submit($form)

    scope.model = {}

    scope.$on 'authorize', ->
      scope.tab = 'login'

    scope.$on 'error', (event) ->
      scope.onError()

    scope.$on 'success', (event) ->
      form.$setPristine()
      scope.onSuccess()

    scope.$on 'timeout', (event) ->
      form.$setPristine()
      scope.onTimeout()

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
