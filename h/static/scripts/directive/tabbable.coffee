# Extend the tabbable directive from angular-bootstrap with autofocus
module.exports = tabbable = ['$timeout', ($timeout) ->
  link: (scope, elem, attrs, ctrl) ->
    return unless ctrl
    render = ctrl.$render
    ctrl.$render = ->
      render.call(ctrl)
      $timeout ->
        elem
        .find(':input')
        .filter(':visible:first')
        .focus()
      , false
  require: '?ngModel'
  restrict: 'C'
]
