'use strict';

var minute = 60;
var hour = minute * 60;

function lessThanThirtySecondsAgo(date, now) {
  return ((now - date) < 30 * 1000);
}

function lessThanOneMinuteAgo(date, now) {
  return ((now - date) < 60 * 1000);
}

function lessThanOneHourAgo(date, now) {
  return ((now - date) < (60 * 60 * 1000));
}

function lessThanOneDayAgo(date, now) {
  return ((now - date) < (24 * 60 * 60 * 1000));
}

function thisYear(date, now) {
  return date.getFullYear() === now.getFullYear();
}

function delta(date, now) {
  return Math.round((now - date) / 1000);
}

function nSec(date, now) {
  return '{} sec'.replace('{}', Math.floor(delta(date, now)));
}

function nMin(date, now) {
  return '{} min'.replace('{}', Math.floor(delta(date, now) / minute));
}

function nHr(date, now) {
  return '{} hr'.replace('{}', Math.floor(delta(date, now) / hour));
}

// Cached DateTimeFormat instances,
// because instantiating a DateTimeFormat is expensive.
var formatters = {};

/**
 * Efficiently return `date` formatted with `options`.
 *
 * This is a wrapper for Intl.DateTimeFormat.format() that caches
 * DateTimeFormat instances because they're expensive to create.
 * Calling Date.toLocaleDateString() lots of times is also expensive in some
 * browsers as it appears to create a new formatter for each call.
 *
 * @returns {string}
 *
 */
function format(date, options, Intl) {
  // If the tests have passed in a mock Intl then use it, otherwise use the
  // real one.
  if (typeof Intl === 'undefined') {
    Intl = window.Intl;
  }

  if (Intl && Intl.DateTimeFormat) {
    var key = JSON.stringify(options);
    var formatter = formatters[key];

    if (!formatter) {
      formatter = formatters[key] = new Intl.DateTimeFormat(undefined,
                                                            options);
    }

    return formatter.format(date);
  } else {
    // IE < 11, Safari <= 9.0.
    return date.toDateString();
  }
}

function dayAndMonth(date, now, Intl) {
  return format(date, {month: 'short', day: '2-digit'}, Intl);
}

function dayAndMonthAndYear(date, now, Intl) {
  return format(date, {day: '2-digit', month: 'short', year: 'numeric'}, Intl);
}

var BREAKPOINTS = [
  {
    test: lessThanThirtySecondsAgo,
    format: function () {return 'Just now';},
    nextUpdate: 1
  },
  {
    test: lessThanOneMinuteAgo,
    format: nSec,
    nextUpdate: 1
  },
  {
    test: lessThanOneHourAgo,
    format: nMin,
    nextUpdate: minute
  },
  {
    test: lessThanOneDayAgo,
    format: nHr,
    nextUpdate: hour
  },
  {
    test: thisYear,
    format: dayAndMonth,
    nextUpdate: null
  },
  {
    test: function () {return true;},
    format: dayAndMonthAndYear,
    nextUpdate: null
  }
];

function getBreakpoint(date, now) {

  // Turn the given ISO 8601 string into a Date object.
  date = new Date(date);

  var breakpoint;
  for (var i = 0; i < BREAKPOINTS.length; i++) {
    breakpoint = BREAKPOINTS[i];
    if (breakpoint.test(date, now)) {
      return breakpoint;
    }
  }
}

function nextFuzzyUpdate(date) {
  if (!date) {
    return null;
  }

  var secs = getBreakpoint(date, new Date()).nextUpdate;

  if (secs === null) {
    return null;
  }

  // We don't want to refresh anything more often than 5 seconds
  secs = Math.max(secs, 5);

  // setTimeout limit is MAX_INT32=(2^31-1) (in ms),
  // which is about 24.8 days. So we don't set up any timeouts
  // longer than 24 days, that is, 2073600 seconds.
  secs = Math.min(secs, 2073600);

  return secs;
}

/**
 * Starts an interval whose frequency decays depending on the relative
 * age of 'date'.
 *
 * This can be used to refresh parts of a UI whose
 * update frequency depends on the age of a timestamp.
 *
 * @return {Function} A function that cancels the automatic refresh.
 */
function decayingInterval(date, callback) {
  var timer;
  var update = function () {
    var fuzzyUpdate = nextFuzzyUpdate(date);
    if (fuzzyUpdate === null) {
      return;
    }
    var nextUpdate = (1000 * fuzzyUpdate) + 500;
    timer = setTimeout(function () {
      callback(date);
      update();
    }, nextUpdate);
  };
  update();

  return function () {
    clearTimeout(timer);
  };
}

/**
 * Formats a date as a string relative to the current date.
 *
 * @param {number} date - The absolute timestamp to format.
 * @return {string} A 'fuzzy' string describing the relative age of the date.
 */
function toFuzzyString(date, Intl) {
  if (!date) {
    return '';
  }
  var now = new Date();

  return getBreakpoint(date, now).format(new Date(date), now, Intl);
}

module.exports = {
  decayingInterval: decayingInterval,
  nextFuzzyUpdate: nextFuzzyUpdate,
  toFuzzyString: toFuzzyString,
};
