assert = chai.assert

describe 'localStorageHelpers', ->
  beforeEach module('h.helpers')

  describe 'failsafe', ->
    fakeWindow  = null
    sandbox = null
    localStorageHelpers = null

    beforeEach module ($provide) ->
      sandbox = sinon.sandbox.create()
      fakeWindow = {
        localStorage: undefined
      }
      $provide.value '$window', fakeWindow
      return

    afterEach ->
      sandbox.restore()

    beforeEach inject (_localStorageHelpers_) ->
      localStorageHelpers = _localStorageHelpers_

    it 'does not throw an exception if localStorage is not supported', ->
      spy = sinon.spy(localStorageHelpers, "setVisibility")
      localStorageHelpers.setVisibility "Test"

      assert.isFalse spy.threw()

    it 'returns undefined when localStorage is not available', ->
      localStorageHelpers.setVisibility 'Test'
      storedVisibility = localStorageHelpers.getVisibility()

      assert.isTrue storedVisibility is undefined

  describe 'privacy', ->
    localStorageHelpers = null

    beforeEach inject (_localStorageHelpers_) ->
      localStorageHelpers = _localStorageHelpers_

    it 'stores the visibility', ->
      visibility = 'public'
      localStorageHelpers.setVisibility visibility
      storedVisibility = localStorageHelpers.getVisibility()

      assert.equal visibility, storedVisibility
