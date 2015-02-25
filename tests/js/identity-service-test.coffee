{module, inject} = require('angular-mock')

assert = chai.assert
sinon.assert.expose assert, prefix: null
sandbox = sinon.sandbox.create()


describe 'h.identity', ->
  provider = null
  mockInjectable = {}

  before ->
    require('../../h/static/scripts/identity-service')

  beforeEach module('h.identity')

  beforeEach module ($provide, identityProvider) ->
    $provide.value('foo', mockInjectable)
    provider = identityProvider
    return

  afterEach ->
    sandbox.restore()

  describe 'identityService', ->
    scope = null
    service = null

    beforeEach inject ($rootScope, identity) ->
      scope = $rootScope
      service = identity

    injects = (name, cb) ->
      it 'invokes identityProvider##{name} with injection', ->
        provider[name] = ['foo', sinon.spy((foo) ->)]
        cb()
        assert.calledWith provider[name][1], mockInjectable

    describe '#logout()', ->
      onlogin = angular.noop
      onlogout = null

      beforeEach ->
        onlogout = sandbox.spy()

      injects 'forgetAuthentication', -> service.logout()

      it 'invokes onlogout on success', ->
        onlogout = sandbox.spy()
        provider.forgetAuthentication = angular.noop
        service.watch({onlogin, onlogout})
        service.logout()
        scope.$digest()
        assert.called onlogout

      it 'does not invoke onlogout on failure', ->
        provider.forgetAuthentication = ($q) -> $q.reject()
        service.watch({onlogin, onlogout})
        service.logout()
        scope.$digest()
        assert.notCalled onlogout

    describe '#request()', ->
      onlogin = null

      beforeEach ->
        onlogin = sandbox.spy()

      injects 'requestAuthentication', -> service.request()

      it 'invokes onlogin with the authorization result on success', ->
        provider.requestAuthentication = -> userid: 'alice'
        service.watch({onlogin})
        service.request()
        scope.$digest()
        assert.calledWith onlogin, sinon.match(userid: 'alice')

      it 'invokes oncancel on failure', ->
        oncancel = sandbox.spy()
        provider.requestAuthentication = ($q) -> $q.reject('canceled')
        service.watch({onlogin})
        service.request({oncancel})
        scope.$digest()
        assert.called oncancel

      it 'does not invoke onlogin on failure', ->
        provider.requestAuthentication = ($q) -> $q.reject('canceled')
        service.watch({onlogin})
        scope.$digest()
        assert.notCalled onlogin

    describe '#watch()', ->
      onlogin = null

      beforeEach ->
        onlogin = sandbox.spy()

      injects 'checkAuthentication', -> service.watch(onlogin: angular.noop)

      it 'requires an onlogin option', ->
        assert.throws (-> service.watch())

      it 'requires callback options to be functions', ->
        assert.throws (-> service.watch(onlogin: angular.noop, onlogout: 'foo'))
        assert.throws (-> service.watch(onlogin: 'foo', onlogout: angular.noop))

      it 'invokes onlogin with the authorization result on success', ->
        provider.checkAuthentication = -> userid: 'alice'
        service.watch({onlogin})
        scope.$digest()
        assert.calledWith onlogin, sinon.match(userid: 'alice')

      it 'does not invoke onlogin on failure', ->
        provider.checkAuthentication = ($q) -> $q.reject('canceled')
        service.watch({onlogin})
        scope.$digest()
        assert.notCalled onlogin

      it 'invokes onready after onlogin on success', ->
        onready = sandbox.spy -> assert.called onlogin
        provider.checkAuthentication = angular.noop
        service.watch({onlogin, onready})
        scope.$digest()
        assert.called onready

      it 'invokes onready on failure', ->
        onready = sandbox.spy()
        provider.checkAuthentication = ($q) -> $q.reject('canceled')
        service.watch({onlogin: angular.noop, onready})
        scope.$digest()
        assert.called onready
