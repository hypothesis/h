assert = chai.assert
sinon.assert.expose(assert, prefix: '')

describe 'h.helpers.formHelpers', ->
  formHelpers = null

  beforeEach module('h.helpers')

  beforeEach inject (_formHelpers_) ->
    formHelpers = _formHelpers_

  describe '.applyValidationErrors', ->
    form = null

    beforeEach ->
      form =
        username: {$setValidity: sinon.spy()}
        password: {$setValidity: sinon.spy()}

    it 'invalidates the "response" input for each error', ->
      formHelpers.applyValidationErrors form,
        username: 'must be at least 3 characters'
        password: 'must be present'

      assert.calledWith(form.username.$setValidity, 'response', false)
      assert.calledWith(form.password.$setValidity, 'response', false)

    it 'adds an error message to each input controller', ->
      formHelpers.applyValidationErrors form,
        username: 'must be at least 3 characters'
        password: 'must be present'

      assert.equal(form.username.responseErrorMessage, 'must be at least 3 characters')
      assert.equal(form.password.responseErrorMessage, 'must be present')
