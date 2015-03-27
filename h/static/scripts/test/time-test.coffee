{module, inject} = require('angular-mock')

assert = chai.assert

minute = 60
hour = minute * 60
day = hour * 24
month = day * 30
year = day * 365


FIXTURES_TO_FUZZY_STRING = [
  [10, 'moments ago']
  [29, 'moments ago']
  [49, '49 seconds ago']
  [minute + 5, 'a minute ago']
  [3 * minute + 5, '3 minutes ago']
  [4 * hour, '4 hours ago']
  [27 * hour, 'a day ago']
  [3 * day + 30 * minute, '3 days ago']
  [6 * month + 2 * day, '6 months ago']
  [1 * year, 'one year ago']
  [1 * year + 2 * month, 'one year ago']
  [2 * year, '2 years ago']
  [8 * year, '8 years ago']
]

FIXTURES_NEXT_FUZZY_UPDATE = [
  [10, 5] # we have a minimum of 5 secs
  [29, 5]
  [49, 5]
  [minute + 5, minute]
  [3 * minute + 5, minute]
  [4 * hour, hour]
  [27 * hour, day]
  [3 * day + 30 * minute, day]
  [6 * month + 2 * day, 24 * day] # longer times are not supported
  [8 * year, 24 * day]            # by setTimout
]

describe 'time', ->
  time = null
  sandbox = null

  before ->
    angular.module('h', []).service('time', require('../time'))

  beforeEach module('h')
  beforeEach inject (_time_) ->
    time = _time_
    sandbox = sinon.sandbox.create()
    sandbox.useFakeTimers()

  afterEach ->
    sandbox.restore()

  describe '.toFuzzyString', ->
    it 'Handles empty dates', ->
      t = null
      expect = ''
      assert.equal(time.toFuzzyString(t), expect)

    testFixture = (f) ->
      ->
        t = new Date()
        expect = f[1]
        sandbox.clock.tick(f[0]*1000)
        assert.equal(time.toFuzzyString(t), expect)

    for f, i in FIXTURES_TO_FUZZY_STRING
      it "creates correct fuzzy string for fixture #{i}", testFixture(f)

  describe '.nextFuzzyUpdate', ->
    it 'Handles empty dates', ->
      t = null
      expect = null
      assert.equal(time.nextFuzzyUpdate(t), expect)

    testFixture = (f) ->
      ->
        t = new Date()
        expect = f[1]
        sandbox.clock.tick(f[0]*1000)
        assert.equal(time.nextFuzzyUpdate(t), expect)

    for f, i in FIXTURES_NEXT_FUZZY_UPDATE
      it "gives correct next fuzzy update time for fixture #{i}", testFixture(f)
