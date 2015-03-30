module.exports = ->
  link: (scope, elem, attr, input) ->
    validate = ->
      scope.$evalAsync ->
        input.$setValidity('match', scope.match == input.$modelValue)

    elem.on('keyup', validate)
    scope.$watch('match', validate)
  scope:
    match: '='
  restrict: 'A'
  require: 'ngModel'
