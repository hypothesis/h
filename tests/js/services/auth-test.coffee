assert = chai.assert
sinon.assert.expose assert, prefix: null

describe 'h', ->
  fakeAnnotator = null
  fakeIdentity = null
  sandbox = null

  beforeEach module('h')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()

    fakeAnnotator = {
      plugins: {
        Auth: {withToken: sandbox.spy()}
      }
      options: {}
      socialView: {name: 'none'}
      addPlugin: sandbox.spy()
    }

    fakeIdentity = {
      watch: sandbox.spy()
      request: sandbox.spy()
    }

    $provide.value 'annotator', fakeAnnotator
    $provide.value 'identity', fakeIdentity
    return

  afterEach ->
    sandbox.restore()


  describe 'auth service', ->
    auth = null

    beforeEach inject (_auth_) ->
      auth = _auth_

    it 'watches the identity service for identity change events', ->
      assert.calledOnce(fakeIdentity.watch)

    it 'sets the persona to null when the identity has been checked', ->
      {onlogin, onlogout, onready} = fakeIdentity.watch.args[0][0]
      onready()
      assert.isNull(auth.user)

