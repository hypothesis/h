{module, inject} = angular.mock

describe 'form-respond', ->
  $scope = null
  formRespond = null
  form = null

  before ->
    angular.module('h', [])
    .service('formRespond', require('../form-respond'))

  beforeEach module('h')
  beforeEach inject (_$rootScope_, _formRespond_) ->
    $scope = _$rootScope_.$new()
    formRespond = _formRespond_
    form =
      $setValidity: sinon.spy()
      username: {$setValidity: sinon.spy()}
      password: {$setValidity: sinon.spy()}

  it 'sets the "response" error key for each field with errors', ->
    formRespond form,
      username: 'must be at least 3 characters'
      password: 'must be present'

    assert.calledWith(form.username.$setValidity, 'response', false)
    assert.calledWith(form.password.$setValidity, 'response', false)

  it 'adds an error message to each input controller', ->
    formRespond form,
      username: 'must be at least 3 characters'
      password: 'must be present'

    assert.equal(form.username.responseErrorMessage, 'must be at least 3 characters')
    assert.equal(form.password.responseErrorMessage, 'must be present')

  it 'sets the "response" error key if the form has a top-level error', ->
    formRespond form, {'': 'Explosions!'}
    assert.calledWith(form.$setValidity, 'response', false)

  it 'adds an error message if the form has a top-level error', ->
    formRespond form, {'': 'Explosions!'}
    assert.equal(form.responseErrorMessage, 'Explosions!')

  it 'sets the "response" error key if the form has a failure reason', ->
    formRespond form, null, 'fail'
    assert.calledWith(form.$setValidity, 'response', false)

  it 'adds an reason message as the response error', ->
    formRespond form, null, 'fail'
    assert.equal(form.responseErrorMessage, 'fail')
