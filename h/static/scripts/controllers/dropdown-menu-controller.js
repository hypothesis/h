'use strict';

var inherits = require('inherits');

var Controller = require('../base/controller');
var setElementState = require('../util/dom').setElementState;

/**
 * Controller for dropdown menus.
 */
function DropdownMenuController(element) {
  Controller.call(this, element);

  var self = this;
  var toggleEl = this.refs.dropdownMenuToggle;

  var handleClickOutside = function (event) {
    if (!self.refs.dropdownMenuContent.contains(event.target)) {
      // When clicking outside the menu on the toggle element, stop the event
      // so that it does not re-trigger the menu
      if (toggleEl.contains(event.target)) {
        event.stopPropagation();
        event.preventDefault();
      }

      self.setState({open: false});

      element.ownerDocument.removeEventListener('click', handleClickOutside,
        true /* capture */);
    }
  };

  toggleEl.addEventListener('click', function (event) {
    event.preventDefault();
    event.stopPropagation();

    self.setState({open: true});

    element.ownerDocument.addEventListener('click', handleClickOutside,
      true /* capture */);
  });
}
inherits(DropdownMenuController, Controller);

DropdownMenuController.prototype.update = function (state) {
  setElementState(this.refs.dropdownMenuContent, {open: state.open});
};

module.exports = DropdownMenuController;
