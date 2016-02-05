// configure error reporting
if (window.RAVEN_CONFIG) {
  require('./raven').init(window.RAVEN_CONFIG);
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
