var CreateGroupFormController = require('./create-group-form');
var DropdownMenuController = require('./dropdown-menu');
var InstallerController = require('./installer-controller');
var ShareGroupFormController = require('./share-group-form');

// load our customized version of Bootstrap which
// provides a few basic UI components (eg. modal dialogs)
require('../styles/vendor/bootstrap/bootstrap');

function setupGroupsController(path) {
  if (path === '/groups/new') {
    new CreateGroupFormController(document.body);
  } else if (document.querySelector('.is-member-of-group')) {
    new ShareGroupFormController(document.body);
  }
}

document.addEventListener('DOMContentLoaded', function () {
  // setup components
  new DropdownMenuController(document);

  // setup route
  var route = document.location.pathname;
  if (route.match('^/(new-homepage)?$')) {
    new InstallerController(document.body);
  } else if (route.match('^/groups') === 0) {
    setupGroupsController(route);
  }
});
