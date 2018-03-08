'use strict';

const Controller = require('../base/controller');

class AdminGroupsController extends Controller {
  constructor(element, options) {
    super(element, options);

    const window_ = options.window || window;
    function confirmFormSubmit() {
      return window_.confirm('This will remove all members from the group, delete all annotations in this group and delete the group permanently. Are you sure?');
    }

    this.on('submit', (event) => {
      if (!confirmFormSubmit()) {
        event.preventDefault();
      }
    });
  }
}

module.exports = AdminGroupsController;
