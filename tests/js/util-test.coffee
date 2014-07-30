assert = chai.assert
sinon.assert.expose(assert, prefix: '')

describe 'h.util', ->
  util = null

  beforeEach module('h.util')

  beforeEach inject (_util_) ->
    util = _util_

  describe '.applyValidationErrors', ->
    form = null

    beforeEach ->
      form =
        username: {$setValidity: sinon.spy()}
        password: {$setValidity: sinon.spy()}

    it 'invalidates the "response" input for each error', ->
      util.applyValidationErrors form,
        username: 'must be at least 3 characters'
        password: 'must be present'

      assert.calledWith(form.username.$setValidity, 'response', false)
      assert.calledWith(form.password.$setValidity, 'response', false)

    it 'adds an error message to each input controller', ->
      util.applyValidationErrors form,
        username: 'must be at least 3 characters'
        password: 'must be present'

      assert.equal(form.username.responseErrorMessage, 'must be at least 3 characters')
      assert.equal(form.password.responseErrorMessage, 'must be present')
