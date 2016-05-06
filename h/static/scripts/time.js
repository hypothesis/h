'use strict';

var minute = 60;
var hour = minute * 60;
var day = hour * 24;
var month = day * 30;
var year = day * 365;

function lessThanThirtySecondsAgo(date, now) {
  return ((now - date) < 30000);
}

function lessThanOneMinuteAgo(date, now) {
  return ((now - date) < 60000);
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
 *
 * @returns {string}
 *
 */
function format(date, options) {
  var key = JSON.stringify(options);
  var formatter = formatters[key];

  if (!formatter) {
    formatter = formatters[key] = new Intl.DateTimeFormat(undefined, options);
  }

  return formatter.format(date);
}

function dayAndMonth(date) {
  return format(date, {
    month: 'short',
    day: '2-digit',
  });
}

function dayAndMonthAndYear(date) {
  return format(date, {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  });
}

var BREAKPOINTS = [
  [lessThanThirtySecondsAgo,    function () {return 'Just now';},      1],
  [lessThanOneMinuteAgo,        nSec,                                  1],
  [lessThanOneHourAgo,          nMin,                                  minute],
  [lessThanOneDayAgo,           nHr,                                   hour],
  [thisYear,                    dayAndMonth,                           month],
  [function () {return true;},  dayAndMonthAndYear,                    year]
];

function getBreakpoint(date, now) {
  var breakpoint;

  for (var i = 0; i < BREAKPOINTS.length; i++) {
    if (BREAKPOINTS[i][0](date, now)) {
      breakpoint = BREAKPOINTS[i];
      break;
    }
  }

  return breakpoint;
}

function nextFuzzyUpdate(date) {
  if (!date) {
    return null;
  }

  var breakpoint = getBreakpoint(date, new Date());
  if (!breakpoint) {
    return null;
  }

  var secs = breakpoint[2];

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
function toFuzzyString(date) {
  if (!date) {
    return '';
  }
  var now = new Date();

  var breakpoint = getBreakpoint(date, now);
  if (!breakpoint) {
    return '';
  }
  return breakpoint[1](new Date(date), now);
}

module.exports = {
  decayingInterval: decayingInterval,
  nextFuzzyUpdate: nextFuzzyUpdate,
  toFuzzyString: toFuzzyString,
};
