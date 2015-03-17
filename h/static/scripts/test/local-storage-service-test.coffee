{module, inject} = require('angular-mock')

assert = chai.assert
sinon.assert.expose assert, prefix: null


describe 'h:localstorage', ->
  fakeWindow = null
  sandbox = null

  before ->
    angular.module('h', [])
    require('../local-storage-service')

  beforeEach module('h')

  describe 'memory fallback', ->
    localstorage = null
    key = null

    beforeEach module ($provide) ->
      sandbox = sinon.sandbox.create()
      fakeWindow = {
        localStorage: {}
      }

      $provide.value '$window', fakeWindow
      return

    afterEach ->
      sandbox.restore()

    beforeEach inject (_localstorage_) ->
      localstorage = _localstorage_
      key = 'test.memory.key'

    it 'sets/gets Item', ->
      value = 'What shall we do with a drunken sailor?'
      localstorage.setItem key, value
      actual = localstorage.getItem key
      assert.equal value, actual

    it 'removes item', ->
      localstorage.setItem key, ''
      localstorage.removeItem key
      result = localstorage.getItem key
      assert.isNull result

    it 'sets/gets Object', ->
      data = {'foo': 'bar'}
      localstorage.setObject key, data
      stringified = localstorage.getItem key
      assert.equal stringified, JSON.stringify data

      actual = localstorage.getObject key
      assert.deepEqual actual, data

  describe 'browser localStorage', ->
    localstorage = null

    beforeEach module ($provide) ->
      sandbox = sinon.sandbox.create()
      fakeWindow = {
        localStorage: {
          getItem: sandbox.stub()
          setItem: sandbox.stub()
          removeItem: sandbox.stub()
        }
      }

      $provide.value '$window', fakeWindow
      return

    afterEach ->
      sandbox.restore()

    beforeEach inject (_localstorage_) ->
      localstorage = _localstorage_

    it 'uses window.localStorage functions to handle data', ->
      key = 'test.storage.key'
      data = 'test data'

      localstorage.setItem key, data
      assert.calledWith fakeWindow.localStorage.setItem, key, data
