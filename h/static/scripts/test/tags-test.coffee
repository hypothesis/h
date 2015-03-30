{module, inject} = require('angular-mock')

assert = chai.assert

describe 'tags', ->
  TAGS_LIST_KEY = 'hypothesis.user.tags.list'
  TAGS_MAP_KEY = 'hypothesis.user.tags.map'

  fakeLocalStorage = null
  sandbox = null
  savedTagsMap = null
  savedTagsList = null
  tags = null

  before ->
    angular.module('h', []).service('tags', require('../tags'))

  beforeEach module('h')
  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()

    fakeStorage = {}
    fakeLocalStorage = {
      getObject: sandbox.spy (key) -> fakeStorage[key]
      setObject: sandbox.spy (key, value) -> fakeStorage[key] = value
      wipe: -> fakeStorage = {}
    }
    $provide.value 'localStorage', fakeLocalStorage
    return

  beforeEach inject (_tags_) ->
    tags = _tags_

  afterEach ->
    sandbox.restore()

  beforeEach ->
    fakeLocalStorage.wipe()

    stamp = Date.now()
    savedTagsMap =
      foo:
        text: 'foo'
        count: 1
        updated: stamp
      bar:
        text: 'bar'
        count: 5
        updated: stamp
      future:
        text: 'future'
        count: 2
        updated: stamp
      argon:
        text: 'argon'
        count: 1
        updated: stamp

    savedTagsList = ['bar', 'future', 'argon', 'foo']

    fakeLocalStorage.setObject TAGS_MAP_KEY, savedTagsMap
    fakeLocalStorage.setObject TAGS_LIST_KEY, savedTagsList

  describe 'filter()', ->
    it 'returns tags having the query as a substring', ->
      assert.deepEqual(tags.filter('a'), ['bar', 'argon'])

    it 'is case insensitive', ->
      assert.deepEqual(tags.filter('Ar'), ['bar', 'argon'])

  describe 'store()', ->
    it 'saves new tags to storage', ->
      tags.store([{text: 'new'}])

      storedTagsList = fakeLocalStorage.getObject TAGS_LIST_KEY
      assert.deepEqual(storedTagsList, ['bar', 'future', 'argon', 'foo', 'new'])

      storedTagsMap = fakeLocalStorage.getObject TAGS_MAP_KEY
      assert.isTrue(storedTagsMap.new?)
      assert.equal(storedTagsMap.new.count, 1)
      assert.equal(storedTagsMap.new.text, 'new')

    it 'increases the count for a tag already stored', ->
      tags.store([{text: 'bar'}])
      storedTagsMap = fakeLocalStorage.getObject TAGS_MAP_KEY
      assert.equal(storedTagsMap.bar.count, 6)

    it 'list is ordered by count desc, lexical asc', ->
      # Will increase from 1 to 6 (as future)
      tags.store([{text: 'foo'}])
      tags.store([{text: 'foo'}])
      tags.store([{text: 'foo'}])
      tags.store([{text: 'foo'}])
      tags.store([{text: 'foo'}])

      storedTagsList = fakeLocalStorage.getObject TAGS_LIST_KEY
      assert.deepEqual(storedTagsList, ['foo', 'bar', 'future', 'argon'])

    it 'gets/sets its objects from the localstore', ->
      tags.store([{text: 'foo'}])

      assert.called(fakeLocalStorage.getObject)
      assert.called(fakeLocalStorage.setObject)
