/**
 * This module implements a very simple and basic categorized logger.
 *
 * If we find we need something more sophisticated, we should consider
 * an established logging library such as Bunyan, Winston etc.
 *
 * Usage:
 *   var logger = getLogger('feature');
 *   logger.{debug, info, warn, error}(fmt, args);
 *
 * When debugging, the logging level for a given logger can be set using
 * logger.setLevel(level) where 'level' is a string (eg. 'debug', 'info').
 *
 * In the browser, all exports of this module are exposed via
 * window.H_DEBUG.logging for runtime adjustment of the logging levels.
 *
 * eg. To turn on debug logging for all loggers, use:
 *
 *  window.H_DEBUG.logging.setLevel('debug'),
 *
 * or for a specific logger:
 *
 *  window.H_DEBUG.logging.getLogger('feature').setLevel('debug')
 */

var assign = require('object-assign');
var loggers = {};

var levels = {
  DEBUG: 5,
  INFO: 10,
  WARN: 20,
  ERROR: 30,
};

var slice = Array.prototype.slice;

var defaultLogLevel = levels.WARN;

function Logger(name) {
  this.name = name;
  this._level = undefined;
}

Logger.prototype.level = function () {
  return this._level || defaultLogLevel;
}

Logger.prototype.logAtLevel = function(level, consoleFn, args) {
  if (level < this.level()) {
    return;
  }
  var fmt = this.name + ': ' + args[0];
  args[0] = fmt;
  consoleFn.apply(console, args);
}

Logger.prototype.debug = function () {
  this.logAtLevel(levels.DEBUG, console.debug, slice.call(arguments));
}

Logger.prototype.info = function () {
  this.logAtLevel(levels.INFO, console.info, slice.call(arguments));
};

Logger.prototype.warn = function () {
  this.logAtLevel(levels.WARN, console.warn, slice.call(arguments));
};

Logger.prototype.error = function () {
  this.logAtLevel(levels.ERROR, console.error, slice.call(arguments));
};

function parseLevel(level) {
  if (typeof level === 'string') {
    var levelKey = level.toUpperCase();
    if (levels.hasOwnProperty(levelKey)) {
      level = levels[levelKey];
    } else {
      throw new Error('Unknown logging level', level);
    }
  }
  return level;
}

/** Set the level for a given logger. This can either be
 * the value of a key in 'levels' (eg. levels.DEBUG)
 * or a case-insensitive key name (eg. 'debug')
 */
Logger.prototype.setLevel = function (level) {
  this._level = parseLevel(level);
};

/** Create or retrieve the logger with a given name.
 *
 * Log levels can be customized per Logger instance.
 */
function getLogger(name) {
  if (!loggers.hasOwnProperty(name)) {
    loggers[name] = new Logger(name);
  }
  return loggers[name];
}

/** Set the default logging level for all loggers.
 * This level will be used by any loggers that do not have custom
 * logging levels set.
 */
function setLevel(level) {
  defaultLogLevel = parseLevel(level);
}

module.exports = {
  levels: levels,
  getLogger: getLogger,
  setLevel: setLevel,
};

/** Expose loggers on the global object
 * for debugging in the browser
 */
window.H_DEBUG = assign(window.H_DEBUG || {}, {
  logging: module.exports
});
