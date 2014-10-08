# Shared helper methods for working with form controllers.
createFormHelpers = ->
  # Takes a FormControllers instance and an object of errors returned by the
  # API and updates the validity of the form. The field.$errors.response
  # property will be true if there are errors and the responseErrorMessage
  # will contain the API error message.
  applyValidationErrors: (form, errors, reason) ->
    for own field, error of errors
      form[field].$setValidity('response', false)
      form[field].responseErrorMessage = error

    form.$setValidity('response', !reason)
    form.responseErrorMessage = reason


formInput = ->
  link: (scope, elem, attr, [form, model, validator]) ->
    return unless form?.$name and model?.$name and validator

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


formValidate = ->
  controller: ->
    controls = {}

    addControl: (control) ->
      if control.$name
        controls[control.$name] = control

    removeControl: (control) ->
      if control.$name
        delete controls[control.$name]

    submit: ->
      # make all the controls dirty and re-render them
      for _, control of controls
        control.$setViewValue(control.$viewValue)
        control.$render()

  link: (scope, elem, attr, ctrl) ->
    elem.on 'submit', ->
      ctrl.submit()


angular.module('h.helpers')
.directive('formInput', formInput)
.directive('formValidate', formValidate)
.factory('formHelpers', createFormHelpers)
