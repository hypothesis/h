module.exports = ['$window', function ($window) {
  return function (value, format) {
    // Determine the timezone name and browser language.
    var timezone = jstz.determine().name();
    var userLang = $window.navigator.language || $window.navigator.userLanguage;

    // Now make a localized date and set the language.
    var momentDate = moment(value);
    momentDate.lang(userLang);

    // Try to localize to the browser's timezone.
    try {
      return momentDate.tz(timezone).format('LLLL');
    } catch (error) {
      // For an invalid timezone, use the default.
      return momentDate.format('LLLL');
    }
  };
}];
