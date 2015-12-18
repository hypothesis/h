var DATE_SUPPORTS_LOCALE_OPTS = (function () {
  try {
    // see http://mzl.la/1YlJJpQ
    (new Date).toLocaleDateString('i');
  } catch (e) {
    if (e instanceof RangeError) {
      return true;
    }
  }
  return false;
})();

/**
 * Returns a standard human-readable representation
 * of a date and time.
 */
function format(date) {
  if (DATE_SUPPORTS_LOCALE_OPTS) {
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      weekday: 'long',
      hour: '2-digit',
      minute: '2-digit',
    });
  } else {
    // IE < 11, Safari <= 9.0.
    // In English, this generates the string most similar to
    // the toLocaleDateString() result above.
    return date.toDateString() + ' ' + date.toLocaleTimeString();
  }
}

module.exports = {
  format: format,
};
