'use strict';

const Controller = require('../base/controller');

class FormSelectOnFocusController extends Controller {
  constructor(element) {
    super(element);

    // In case the `focus` event has already been fired, select the element
    if (element === document.activeElement) {
      element.select();
    }

    element.addEventListener('focus', (event) => {
      event.target.select();
    });
  }
}

module.exports = FormSelectOnFocusController;
