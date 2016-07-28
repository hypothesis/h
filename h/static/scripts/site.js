'use strict';

// configure error reporting
var settings = require('./settings')(document);
if (settings.raven) {
  require('./raven').init(settings.raven);
}

require('./polyfills');

var page = require('./page');

var CreateGroupFormController = require('./create-group-form');
var FormSelectOnFocusController = require('./form-select-onfocus-controller');

page('/groups/new', function () {
  new CreateGroupFormController(document.body);
});

page('/login', function() {
  new FormSelectOnFocusController(document.body);
});

page('/register', function() {
  new FormSelectOnFocusController(document.body);
});

page('/forgot_password', function() {
  new FormSelectOnFocusController(document.body);
});
