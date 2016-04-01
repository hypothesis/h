SearchFilter = require('../search-filter')

describe 'searchFilter', ->
  searchFilter = null

  beforeEach ->
    searchFilter = new SearchFilter()

  describe 'toObject', ->
    it 'puts a simple search string under the any filter', ->
      query = 'foo'
      result = searchFilter.toObject(query)
      assert.equal(result.any[0], query)

    it 'uses the filters as keys in the result object', ->
      query = 'id:anid user:john text:foo quote:bar group:agroup other'
      result = searchFilter.toObject(query)
      assert.equal(result.any[0], 'other')
      assert.equal(result.user[0], 'john')
      assert.equal(result.text[0], 'foo')
      assert.equal(result.quote[0], 'bar')
      assert.equal(result.group[0], 'agroup')
      assert.equal(result.id[0], 'anid')

    it 'collects the same filters into a list', ->
      query = 'user:john text:foo quote:bar other user:doe text:fuu text:fii'
      result = searchFilter.toObject(query)
      assert.equal(result.any[0], 'other')
      assert.equal(result.user[0], 'john')
      assert.equal(result.user[1], 'doe')
      assert.equal(result.text[0], 'foo')
      assert.equal(result.text[1], 'fuu')
      assert.equal(result.text[2], 'fii')
      assert.equal(result.quote[0], 'bar')

    it 'preserves data with semicolon characters', ->
      query = 'uri:http://test.uri'
      result = searchFilter.toObject(query)
      assert.equal(result.uri[0], 'http://test.uri')

    it 'collects valid filters and puts invalid into the any category', ->
      query = 'uri:test foo:bar text:hey john:doe quote:according hi-fi a:bc'
      result = searchFilter.toObject(query)
      assert.isFalse(result.foo?)
      assert.isFalse(result.john?)
      assert.isFalse(result.a?)
      assert.equal(result.uri[0], 'test')
      assert.equal(result.text[0], 'hey')
      assert.equal(result.quote[0], 'according')
      assert.equal(result.any[0], 'foo:bar')
      assert.equal(result.any[1], 'john:doe')
      assert.equal(result.any[2], 'hi-fi')
      assert.equal(result.any[3], 'a:bc')

  describe '#generateFacetedFilter', ->
    it 'populates facets', ->
      facets = ['quote','result','tag','text','uri','user','id']
      for facet in facets
        query = facet + ':sometoken'
        filter = searchFilter.generateFacetedFilter(query)
        assert.deepEqual(filter[facet], {
          terms: ['sometoken'],
          operator: filter[facet].operator,
        })

    it 'puts other terms in the "any" facet', ->
      filter = searchFilter.generateFacetedFilter('foo bar')
      assert.deepEqual(filter.any, {
        terms: ['foo', 'bar'],
        operator: 'and',
      })
