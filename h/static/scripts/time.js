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

function lessThanTwoMinutesAgo(date, now) {
  return ((now - date) < 120000);
}

function lessThanOneHourAgo(date, now) {
  return ((now - date) < (60 * 60 * 1000));
}

function lessThanTwoHoursAgo(date, now) {
  return ((now - date) < (120 * 60 * 1000));
}

function lessThanOneDayAgo(date, now) {
  return ((now - date) < (24 * 60 * 60 * 1000));
}

function lessThanTwoDaysAgo(date, now) {
  return ((now - date) < (48 * 60 * 60 * 1000));
}

function lessThanThirtyDaysAgo(date, now) {
  return ((now - date) < (30 * 24 * 60 * 60 * 1000));
}

function lessThanOneYearAgo(date, now) {
  // Here we approximate "one year" as being a calendar year and not a leap
  // year: 365 days.
  return ((now - date) < (365 * 24 * 60 * 60 * 1000));
}

function lessThanTwoYearsAgo(date, now) {
  // Here we approximate "one year" as being a calendar year and not a leap
  // year: 365 days.
  return ((now - date) < (2 * 365 * 24 * 60 * 60 * 1000));
}

var BREAKPOINTS = [
  [lessThanThirtySecondsAgo,    'moments ago',     1],
  [lessThanOneMinuteAgo,        '{} seconds ago',  1],
  [lessThanTwoMinutesAgo,       'a minute ago',    minute],
  [lessThanOneHourAgo,          '{} minutes ago',  minute],
  [lessThanTwoHoursAgo,         'an hour ago',     hour],
  [lessThanOneDayAgo,           '{} hours ago',    hour],
  [lessThanTwoDaysAgo,          'a day ago',       day],
  [lessThanThirtyDaysAgo,       '{} days ago',     day],
  [lessThanOneYearAgo,          '{} months ago',   month],
  [lessThanTwoYearsAgo,         'one year ago',    year],
  [function () {return true;},  '{} years ago',    year]
];

function getBreakpoint(date) {
  var breakpoint;
  var now = new Date();

  for (var i = 0; i < BREAKPOINTS.length; i++) {
    if (BREAKPOINTS[i][0](date, now)) {
      breakpoint = BREAKPOINTS[i];
      break;
    }
  }

  return {
    delta: Math.round((new Date() - new Date(date)) / 1000),
    breakpoint: breakpoint,
  };
}

function nextFuzzyUpdate(date) {
  if (!date) {
    return null;
  }

  var breakpoint = getBreakpoint(date).breakpoint;
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
  var breakpointInfo = getBreakpoint(date);
  var breakpoint = breakpointInfo.breakpoint;
  var delta = breakpointInfo.delta;
  if (!breakpoint) {
    return '';
  }
  var template = breakpoint[1];
  var resolution = breakpoint[2];
  return template.replace('{}', String(Math.floor(delta / resolution)));
}

module.exports = {
  decayingInterval: decayingInterval,
  nextFuzzyUpdate: nextFuzzyUpdate,
  toFuzzyString: toFuzzyString,
};
