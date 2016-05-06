'use strict';

var time = require('../time');

var minute = 60;
var hour = minute * 60;
var day = hour * 24;
var month = day * 30;
var year = day * 365;

var FIXTURES_TO_FUZZY_STRING = [
  [10, 'Just now'],
  [29, 'Just now'],
  [49, '49 sec'],
  [minute + 5, '1 min'],
  [3 * minute + 5, '3 min'],
  [hour, '1 hr'],
  [4 * hour, '4 hr'],
  [27 * hour, '01 Jan'],
  [3 * day + 30 * minute, '01 Jan'],
  [6 * month + 2 * day, '01 Jan'],
  [1 * year, '01 Jan 1970'],
  [1 * year + 2 * month, '01 Jan 1970'],
  [2 * year, '01 Jan 1970'],
  [8 * year, '01 Jan 1970']
];

var FIXTURES_NEXT_FUZZY_UPDATE = [
  [10, 5], // we have a minimum of 5 secs
  [29, 5],
  [49, 5],
  [minute + 5, minute],
  [3 * minute + 5, minute],
  [4 * hour, hour],
  [27 * hour, day],
  [3 * day + 30 * minute, day],
  [6 * month + 2 * day, 24 * day], // longer times are not supported
  [8 * year, 24 * day]            // by setTimout
];

describe('time', function () {
  var sandbox;

  beforeEach(function () {
    sandbox = sinon.sandbox.create();
    sandbox.useFakeTimers();
  });

  afterEach(function () {
    sandbox.restore();
  });

  describe('.toFuzzyString', function () {

    var originalIntl;

    before(function () {

      // Intl isn't implemented in PhantomJS so we have to mock it in these
      // tests. The mock version returns the results we'd expect from the real
      // one for the test values that we use.
      originalIntl = window.Intl;
      window.Intl = {
        DateTimeFormat: function () {
          return {
            format: function () {
              if (new Date().getYear() === 70) {
                return '01 Jan';
              } else {
                return '01 Jan 1970';
              }
            }
          };
        }
      };
    });

    after(function () {
      window.Intl = originalIntl;
    });

    it('Handles empty dates', function () {
      var t = null;
      var expect = '';
      assert.equal(time.toFuzzyString(t), expect);
    });

    var testFixture = function (f) {
      return function () {
        var t = new Date();
        var expect = f[1];
        sandbox.clock.tick(f[0] * 1000);
        assert.equal(time.toFuzzyString(t), expect);
      };
    };

    for (var i = 0, f; i < FIXTURES_TO_FUZZY_STRING.length; i++) {
      f = FIXTURES_TO_FUZZY_STRING[i];
      it('creates correct fuzzy string for fixture ' + i,
        testFixture(f));
    }
  });

  describe('.decayingInterval', function () {
    it('uses a short delay for recent timestamps', function () {
      var date = new Date();
      var callback = sandbox.stub();
      time.decayingInterval(date, callback);
      sandbox.clock.tick(6 * 1000);
      assert.calledWith(callback, date);
      sandbox.clock.tick(6 * 1000);
      assert.calledTwice(callback);
    });

    it('uses a longer delay for older timestamps', function () {
      var date = new Date();
      var ONE_MINUTE = minute * 1000;
      sandbox.clock.tick(10 * ONE_MINUTE);
      var callback = sandbox.stub();
      time.decayingInterval(date, callback);
      sandbox.clock.tick(ONE_MINUTE / 2);
      assert.notCalled(callback);
      sandbox.clock.tick(ONE_MINUTE);
      assert.calledWith(callback, date);
      sandbox.clock.tick(ONE_MINUTE);
      assert.calledTwice(callback);
    });

    it('returned function cancels the timer', function () {
      var date = new Date();
      var callback = sandbox.stub();
      var cancel = time.decayingInterval(date, callback);
      cancel();
      sandbox.clock.tick(minute * 1000);
      assert.notCalled(callback);
    });
  });

  describe('.nextFuzzyUpdate', function () {
    it('Handles empty dates', function () {
      var t = null;
      var expect = null;
      assert.equal(time.nextFuzzyUpdate(t), expect);
    });

    var testFixture = function (f) {
      return function () {
        var t = new Date();
        var expect = f[1];
        sandbox.clock.tick(f[0] * 1000);
        assert.equal(time.nextFuzzyUpdate(t), expect);
      };
    };

    for (var i = 0, f; i < FIXTURES_NEXT_FUZZY_UPDATE.length; i++) {
      f = FIXTURES_NEXT_FUZZY_UPDATE[i];
      it('gives correct next fuzzy update time for fixture ' + i,
        testFixture(f));
    }
  });
});
