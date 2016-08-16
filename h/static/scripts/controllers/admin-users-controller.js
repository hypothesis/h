'use strict';

function AdminUsersController(element, window_) {
  window_ = window_ || window;

  this._form = element;

  function confirmFormSubmit() {
    return window_.confirm('This will permanently delete all the user\'s data. Are you sure?');
  }

  this._form.addEventListener('submit', function (event) {
    if (!confirmFormSubmit()) {
      event.preventDefault();
    }
  });
}

module.exports = AdminUsersController;
