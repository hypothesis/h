'use strict';

function FormSelectOnFocusController(root) {
  this._elements = root.querySelectorAll('.js-select-onfocus');

  for (var i = 0; i < this._elements.length; i++) {
    var element = this._elements[i];

    // In case the `focus` event has already been fired, select the element
    if (element === document.activeElement) {
      element.select();
    }

    element.addEventListener('focus', function(event) {
      event.target.select();
    });
  }
}

module.exports = FormSelectOnFocusController;
