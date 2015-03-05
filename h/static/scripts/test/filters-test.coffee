{module, inject} = require('angular-mock')

assert = chai.assert
sinon.assert.expose assert, prefix: null

describe 'h:filters', ->

  before ->
    angular.module('h', [])
    require('../filters')

  describe 'persona', ->
    filter = null
    term = 'acct:hacker@example.com'

    beforeEach module('h')
    beforeEach inject ($filter) ->
      filter = $filter('persona')

    it 'should return the whole term by request', ->
      result = filter('acct:hacker@example.com', 'term')
      assert.equal result, 'acct:hacker@example.com'

    it 'should return the requested part', ->
      assert.equal filter(term), 'hacker'
      assert.equal filter(term, 'term'), term,
      assert.equal filter(term, 'username'), 'hacker'
      assert.equal filter(term, 'provider'), 'example.com'

    it 'should pass through unrecognized terms as username or term', ->
      assert.equal filter('bogus'), 'bogus'
      assert.equal filter('bogus', 'username'), 'bogus'

    it 'should handle error cases', ->
      assert.notOk filter()
      assert.notOk filter('bogus', 'provider')

  describe 'urlencode', ->
    filter = null

    beforeEach module('h')
    beforeEach inject ($filter) ->
      filter = $filter('urlencode')

    it 'encodes reserved characters in the term', ->
      assert.equal(filter('#hello world'), '%23hello%20world')
