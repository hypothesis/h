assert = chai.assert
sandbox = sinon.sandbox.create()

minute = 60
hour = minute * 60
day = hour * 24
month = day * 30
year = day * 365

FIXTURES_TO_TEST = [
  [10, 'moments ago', 20]
  [29, 'moments ago', 1]
  [49, '49 seconds ago', 1]
  [minute + 5, 'a minute ago', 55]
  [3 * minute + 5, '3 minutes ago', minute]
  [4 * hour, '4 hours ago', hour]
  [27 * hour, 'yesterday', 21*hour]
  [3 * day + 30 * minute, '3 days ago', day]
  [6 * month + 2 * day, '6 months ago', month]
  [8 * year, '8 years ago', year]
]

describe 'timeHelpers', ->
  beforeEach module('h.helpers')
  timeHelpers = null

  beforeEach inject (_timeHelpers_) ->
    timeHelpers = _timeHelpers_
    sandbox.useFakeTimers()

  afterEach ->
    sandbox.restore()


  describe 'timestamp', ->
    it 'Handles undefined', ->
      time = undefined
      {message, updateAt} = timeHelpers.timestamp time
      assert.equal(message, '')
      assert.equal(updateAt, 5)

    it 'it counts the seconds', ->
      time = new Date()
      sandbox.clock.tick(5000)

      timeHelpers.timestamp time
      sandbox.clock.tick(1000)

      {message, updateAt} = timeHelpers.timestamp time
      assert.equal(message, 'moments ago')
      assert.equal(updateAt, 24)


    testFixture = (f) ->
      ->
        time = new Date()
        sandbox.clock.tick(f[0]*1000)
        {message, updateAt} = timeHelpers.timestamp time
        assert.equal(message, f[1])
        assert.equal(updateAt, f[2])

    for f,i in FIXTURES_TO_TEST
      it 'gives correct next fuzzy update time for fixture #{i}', testFixture(f)
