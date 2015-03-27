{module, inject} = require('angular-mock')

assert = chai.assert
sinon.assert.expose assert, prefix: null


describe 'localStorage', ->
  fakeWindow = null
  sandbox = null

  before ->
    angular.module('h', [])
    .service('localStorage', require('../local-storage'))

  beforeEach module('h')

  describe 'memory fallback', ->
    localStorage = null
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

    beforeEach inject (_localStorage_) ->
      localStorage = _localStorage_
      key = 'test.memory.key'

    it 'sets/gets Item', ->
      value = 'What shall we do with a drunken sailor?'
      localStorage.setItem key, value
      actual = localStorage.getItem key
      assert.equal value, actual

    it 'removes item', ->
      localStorage.setItem key, ''
      localStorage.removeItem key
      result = localStorage.getItem key
      assert.isNull result

    it 'sets/gets Object', ->
      data = {'foo': 'bar'}
      localStorage.setObject key, data
      stringified = localStorage.getItem key
      assert.equal stringified, JSON.stringify data

      actual = localStorage.getObject key
      assert.deepEqual actual, data

  describe 'browser localStorage', ->
    localStorage = null

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

    beforeEach inject (_localStorage_) ->
      localStorage = _localStorage_

    it 'uses window.localStorage functions to handle data', ->
      key = 'test.storage.key'
      data = 'test data'

      localStorage.setItem key, data
      assert.calledWith fakeWindow.localStorage.setItem, key, data
