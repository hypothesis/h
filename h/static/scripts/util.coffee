util = ->
  applyValidationErrors: (form, errors) ->
    for own field, error of errors
      form[field].$setValidity('response', false)
      form[field].responseErrorMessage = error


angular.module('h.util', []).service('util', util)
