imports = [
  'h.flash'
]


class AuthController
  this.$inject = ['$scope', '$timeout', 'flash']
  constructor:   ( $scope,   $timeout,   flash ) ->
    auth = this
    base =
      username: null
      email: null
      password: null
      code: null
    timeout = null

    this.reset = ->
      delete $scope.errors
      angular.extend $scope.model, base
      for own _, ctrl of $scope when typeof ctrl?.$setPristine is 'function'
        ctrl.$setPristine()

    this.submit = (form) ->
      return unless form.$valid
      $scope.model
      $scope.model["$#{form.$name}"]().then $scope.reset, (data) ->
        {errors, reason} = data
        $scope.errors = session: reason
        $scope.errors[form] = {}
        for field, error of errors
          $scope.errors[form][field] = error

    $scope.$on '$destroy', ->
      if timeout
        $timeout.cancel timeout

    $scope.$watchCollection 'model', ->
      # Reset the auth forms after five minutes of inactivity
      if timeout
        $timeout.cancel timeout

      timeout = $timeout ->
        for key of base
          if $scope.model[key]
            auth.reset()
            flash 'info',
              'For your security, the forms have been reset due to inactivity.'
      , 3000000


auth = ->
  controller: 'AuthController'
  link: (scope, elem, attrs, ctrl) ->
    scope.$watch attrs.auth, (value) ->
      scope.model = value
      scope.reset = ctrl.reset
      scope.submit = ctrl.submit
  scope: true


angular.module('h.auth', imports)
.controller('AuthController', AuthController)
.directive('auth', auth)
