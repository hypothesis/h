{module, inject} = angular.mock

describe 'h', ->
  fakeAnnotator = null
  fakeIdentity = null
  sandbox = null

  before ->
    angular.module('h', [])
    .factory('auth', require('../auth'))

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
    $http = null
    auth = null

    beforeEach inject (_$http_, _auth_) ->
      $http = _$http_
      auth = _auth_

    it 'watches the identity service for identity change events', ->
      assert.calledOnce(fakeIdentity.watch)

    it 'sets the user to null when the identity has been checked', ->
      {onready} = fakeIdentity.watch.args[0][0]
      onready()
      assert.isNull(auth.user)

    describe 'at login', ->
      beforeEach ->
        {onlogin} = fakeIdentity.watch.args[0][0]
        onlogin('test-assertion')
        fakeToken = { userId: 'acct:hey@joe'}
        fakeAnnotator.plugins.Auth.token = 'test-token'
        userSetter = fakeAnnotator.plugins.Auth.withToken.args[0][0]
        userSetter(fakeToken)

      it 'sets auth.user', ->
        assert.equal(auth.user, 'acct:hey@joe')

      it 'sets the token header as a default header', ->
        token = $http.defaults.headers.common['X-Annotator-Auth-Token']
        assert.equal(token, 'test-token')

    describe 'at logout', ->
      authPlugin = null

      beforeEach ->
        {onlogout} = fakeIdentity.watch.args[0][0]
        auth.user = 'acct:hey@joe'
        authPlugin = fakeAnnotator.plugins.Auth
        onlogout()

      it 'destroys the plugin', ->
        assert.called(authPlugin.destroy)

      it 'sets auth.user to null', ->
        assert.equal(auth.user, null)

      it 'unsets the token header', ->
        token = $http.defaults.headers.common['X-Annotator-Auth-Token']
        assert.isUndefined(token)
