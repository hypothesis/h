# Shared helper methods for working with form controllers.
createFormHelpers = ->
  # Takes a FormControllers instance and an object of errors returned by the
  # API and updates the validity of the form. The field.$errors.response
  # property will be true if there are errors and the responseErrorMessage
  # will contain the API error message.
  applyValidationErrors: (form, errors) ->
    for own field, error of errors
      form[field].$setValidity('response', false)
      form[field].responseErrorMessage = error


angular.module('h.helpers.formHelpers', [])
.factory('formHelpers', createFormHelpers)
