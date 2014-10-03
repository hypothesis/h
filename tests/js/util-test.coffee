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
        $setValidity: sinon.spy()
        username: {$setValidity: sinon.spy()}
        password: {$setValidity: sinon.spy()}

    it 'sets the "response" error key for each field with errors', ->
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

    it 'sets the "response" error key if the form has a failure reason', ->
      formHelpers.applyValidationErrors form, null, 'fail'
      assert.calledWith(form.$setValidity, 'response', false)

    it 'adds an reason message as the response error', ->
      formHelpers.applyValidationErrors form, null, 'fail'
      assert.equal(form.responseErrorMessage, 'fail')
