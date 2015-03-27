module.exports = ->
  link: (scope, elem, attr, [form, model, validator]) ->
    return unless form?.$name and model.$name and validator

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

    validator.addControl(model)
    scope.$on '$destroy', -> validator.removeControl this

    scope.$watch ->
      if model.$modelValue? or model.$pristine
        toggleClass(model.$invalid and model.$dirty)
      return

  require: ['^?form', '?ngModel', '^?formValidate']
  restrict: 'C'
