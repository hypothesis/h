var CreateGroupFormController = require('./create-group-form');
var DropdownMenuController = require('./dropdown-menu');
var ShareGroupFormController = require('./share-group-form');

var envTest = require('./browser-env-test');

// load our customized version of Bootstrap which
// provides a few basic UI components (eg. modal dialogs)
require('./vendor/bootstrap');

function setupGroupsController(path) {
  if (path === '/groups/new') {
    new CreateGroupFormController(document.body);
  } else if (document.querySelector('.is-member-of-group')) {
    new ShareGroupFormController(document.body);
  }
}

document.addEventListener('DOMContentLoaded', function () {
  if (document.location.pathname.indexOf('/groups') === 0) {
    setupGroupsController(document.location.pathname);
  }

  // setup components
  new DropdownMenuController(document);

  // show/hide elements depending on the environment
  envTest.showSupportedElements(document);
});
