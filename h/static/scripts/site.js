var CreateGroupFormController = require('./create-group-form');
var DropdownMenuController = require('./dropdown-menu');
var ShareGroupFormController = require('./share-group-form');

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

  new DropdownMenuController(document);
});
