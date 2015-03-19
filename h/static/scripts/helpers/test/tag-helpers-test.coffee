{module, inject} = require('angular-mock')

assert = chai.assert

describe 'h.helpers:tag-helpers', ->
  TAGS_LIST_KEY = 'hypothesis.user.tags.list'
  TAGS_MAP_KEY = 'hypothesis.user.tags.map'

  fakeLocalStorage = null
  sandbox = null
  savedTagsMap = null
  savedTagsList = null
  tagHelpers = null

  before ->
    angular.module('h.helpers', [])
    require('../tag-helpers')

  beforeEach module('h.helpers')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()

    fakeStorage = {}
    fakeLocalStorage = {
      getObject: sandbox.spy (key) -> fakeStorage[key]
      setObject: sandbox.spy (key, value) -> fakeStorage[key] = value
      wipe: -> fakeStorage = {}
    }
    $provide.value 'localstorage', fakeLocalStorage
    return

  beforeEach inject (_tagHelpers_) ->
    tagHelpers = _tagHelpers_

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

  describe 'filterTags()', ->
    it 'returns tags having the query as a substring', ->
      tags = tagHelpers.filterTags('a')
      assert.deepEqual(tags, ['bar', 'argon'])

    it 'is case insensitive', ->
      tags = tagHelpers.filterTags('Ar')
      assert.deepEqual(tags, ['bar', 'argon'])

  describe 'storeTags()', ->
    it 'saves new tags to storage', ->
      tags = [{text: 'new'}]
      tagHelpers.storeTags(tags)

      storedTagsList = fakeLocalStorage.getObject TAGS_LIST_KEY
      assert.deepEqual(storedTagsList, ['bar', 'future', 'argon', 'foo', 'new'])

      storedTagsMap = fakeLocalStorage.getObject TAGS_MAP_KEY
      assert.isTrue(storedTagsMap.new?)
      assert.equal(storedTagsMap.new.count, 1)
      assert.equal(storedTagsMap.new.text, 'new')

    it 'increases the count for a tag already stored', ->
      tags = [{text: 'bar'}]
      tagHelpers.storeTags(tags)
      storedTagsMap = fakeLocalStorage.getObject TAGS_MAP_KEY
      assert.equal(storedTagsMap.bar.count, 6)

    it 'list is ordered by count desc, lexical asc', ->
      # Will increase from 1 to 6 (as future)
      tags = [{text: 'foo'}]

      tagHelpers.storeTags(tags)
      tagHelpers.storeTags(tags)
      tagHelpers.storeTags(tags)
      tagHelpers.storeTags(tags)
      tagHelpers.storeTags(tags)

      storedTagsList = fakeLocalStorage.getObject TAGS_LIST_KEY
      assert.deepEqual(storedTagsList, ['foo', 'bar', 'future', 'argon'])

    it 'gets/sets its objects from the localstore', ->
      tags = [{text: 'foo'}]
      tagHelpers.storeTags(tags)

      assert.called(fakeLocalStorage.getObject)
      assert.called(fakeLocalStorage.setObject)
