'use strict';

var Controller = require('../base/controller');

class AdminUsersController extends Controller {
  constructor(element, window_ = window) {
    super(element);

    function confirmFormSubmit() {
      return window_.confirm('This will permanently delete all the user\'s data. Are you sure?');
    }

    this.element.addEventListener('submit', event => {
      if (!confirmFormSubmit()) {
        event.preventDefault();
      }
    });
  }
}

module.exports = AdminUsersController;
