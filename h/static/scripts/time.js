'use strict';

var minute = 60;
var hour = minute * 60;
var day = hour * 24;
var month = day * 30;
var year = day * 365;

var BREAKPOINTS = [
  [30,         'moments ago',    1],
  [minute,     '{} seconds ago', 1],
  [2 * minute, 'a minute ago',   minute],
  [hour,       '{} minutes ago', minute],
  [2 * hour,   'an hour ago',    hour],
  [day,        '{} hours ago',   hour],
  [2 * day,    'a day ago',      day],
  [month,      '{} days ago',    day],
  [year,       '{} months ago',  month],
  [2 * year,   'one year ago',   year],
  [Infinity,   '{} years ago',   year]
];

function getBreakpoint(date) {
  var delta = Math.round((new Date() - new Date(date)) / 1000);
  var breakpoint;

  for (var i = 0; i < BREAKPOINTS.length; i++) {
    if (BREAKPOINTS[i][0] > delta) {
      breakpoint = BREAKPOINTS[i];
      break;
    }
  }

  return {
    delta: delta,
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
