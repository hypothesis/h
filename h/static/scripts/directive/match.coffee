module.exports = ->
  link: (scope, elem, attr, input) ->
    input.$validators.match = (modelValue) ->
      return scope.match == modelValue
  scope:
    match: '='
  restrict: 'A'
  require: 'ngModel'
