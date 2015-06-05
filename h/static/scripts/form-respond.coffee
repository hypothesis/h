# Takes a FormController instance and an object of errors returned by the
# API and updates the validity of the form. The field.$errors.response
# property will be true if there are errors and the responseErrorMessage
# will contain the API error message.
module.exports = ->
  (form, errors, reason) ->
    form.$setValidity('response', !reason)
    form.responseErrorMessage = reason

    for own field, error of errors
      # If there's an empty-string field, it's a top-level form error. Set the
      # overall form validity from this field, but only if there wasn't already
      # a reason.
      if !reason and field == ''
        form.$setValidity('response', false)
        form.responseErrorMessage = error
        continue

      form[field].$setValidity('response', false)
      form[field].responseErrorMessage = error
