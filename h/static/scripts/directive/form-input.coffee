module.exports = ->
  link: (scope, elem, attr, [model, validator]) ->
    return unless model

    fieldClassName = 'form-field'
    errorClassName = 'form-field-error'

    render = model.$render

    resetResponse = (value) ->
      model.$setValidity('response', true)
      value

    toggleClass = (addClass) ->
      elem.toggleClass(errorClassName, addClass)
      elem.parent().toggleClass(errorClassName, addClass)

    model.$parsers.unshift(resetResponse)
    model.$render = ->
      toggleClass(model.$invalid and model.$dirty)
      render()

    if validator?
      validator.addControl(model)
      scope.$on '$destroy', -> validator.removeControl model

    scope.$watch ->
      if model.$modelValue? or model.$pristine
        toggleClass(model.$invalid and model.$dirty)
      return

  require: ['?ngModel', '^?formValidate']
  restrict: 'C'
