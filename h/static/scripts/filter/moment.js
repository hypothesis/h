var moment = require('moment');


module.exports = ['$window', function ($window) {
  return function (value, format) {
    return moment(value).format(format);
  };
}];
