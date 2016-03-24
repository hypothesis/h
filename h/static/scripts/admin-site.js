'use strict';

// configure error reporting
var settings = require('./settings')(document);
if (settings.raven) {
  require('./raven').init(settings.raven);
}

window.$ = window.jQuery = require('jquery');
require('bootstrap');

var page = require('page');

document.addEventListener('DOMContentLoaded', function () {
  page.start();
});
