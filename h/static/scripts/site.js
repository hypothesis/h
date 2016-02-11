// configure error reporting
var settings = require('./settings')(document);
if (settings.raven) {
  require('./raven').init(settings.raven);
}

var page = require('page');

var CreateGroupFormController = require('./create-group-form');
var DropdownMenuController = require('./dropdown-menu');
var InstallerController = require('./installer-controller');
var ShareGroupFormController = require('./share-group-form');

// setup components
new DropdownMenuController(document);

page('/', function () {
  // load our customized version of Bootstrap which
  // provides a few basic UI components (eg. modal dialogs)
  require('../styles/vendor/bootstrap/bootstrap');
  new InstallerController(document.body);
});

page('/groups/new', function () {
  new CreateGroupFormController(document.body);
});

document.addEventListener('DOMContentLoaded', function () {
  page.start();
});
