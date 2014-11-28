assert = chai.assert

describe 'localStorageHelpers', ->
  beforeEach module('h.helpers')

  describe 'fallback', ->
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

    it 'uses memoryStorage when localStorage is not available', ->
      visibility = 'private'
      localStorageHelpers.setVisibility visibility
      storedVisibility = localStorageHelpers.getVisibility()

      assert.equal storedVisibility, visibility

  describe 'visibility', ->
    localStorageHelpers = null

    beforeEach inject (_localStorageHelpers_) ->
      localStorageHelpers = _localStorageHelpers_

    it 'stores the visibility', ->
      visibility = 'public'
      localStorageHelpers.setVisibility visibility
      storedVisibility = localStorageHelpers.getVisibility()

      assert.equal visibility, storedVisibility
