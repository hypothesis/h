'use strict';

function FormSelectOnFocusController(element) {
  // In case the `focus` event has already been fired, select the element
  if (element === document.activeElement) {
    element.select();
  }

  element.addEventListener('focus', function(event) {
    event.target.select();
  });
}

module.exports = FormSelectOnFocusController;
