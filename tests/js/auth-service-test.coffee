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
        Auth:{
          withToken: sandbox.spy()
          destroy: sandbox.spy()
          element: {removeData: sandbox.spy()}
        }
        Permissions: {
          destroy: sandbox.spy()
          setUser: sandbox.spy()
        }
      }
      options: {}
      socialView: {name: 'none'}
      addPlugin: sandbox.spy()
    }

    fakeIdentity ={
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

    it 'sets the user to null when the identity has been checked', ->
      {onready} = fakeIdentity.watch.args[0][0]
      onready()
      assert.isNull(auth.user)

    it 'sets the Permissions plugin and sets auth.user at login', ->
      {onlogin} = fakeIdentity.watch.args[0][0]
      onlogin('test-assertion')
      fakeToken = { userId: 'acct:hey@joe'}
      userSetter = fakeAnnotator.plugins.Auth.withToken.args[0][0]
      userSetter(fakeToken)
      assert.equal(auth.user, 'acct:hey@joe')
      secondPlugin = fakeAnnotator.addPlugin.args[1]
      assert.equal(secondPlugin[0], 'Permissions')

    it 'destroys the plugins at logout and sets auth.user to null', ->
      {onlogout} = fakeIdentity.watch.args[0][0]
      auth.user = 'acct:hey@joe'
      authPlugin = fakeAnnotator.plugins.Auth
      permissionsPlugin = fakeAnnotator.plugins.Permissions
      onlogout()

      assert.called(authPlugin.destroy)
      assert.called(permissionsPlugin.destroy)
      assert.equal(auth.user, null)

