'use strict';

function AdminUsersController(element, window_) {
  this._form = element.querySelector('#js-users-delete-form');

  function confirmFormSubmit() {
    return window_.confirm('This will permanently delete all the user\'s data. Are you sure?');
  }

  if (this._form) {
    this._form.addEventListener('submit', function (event) {
      if (!confirmFormSubmit()) {
        event.preventDefault();
      }
    });
  }
}

module.exports = AdminUsersController;
