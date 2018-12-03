'use strict';

const Controller = require('../base/controller');

/**
 * Button for closing an alert dialog.
 */
class AlertCloseButtonController extends Controller {
  constructor(element, options) {
    super(element, options);

    const window_ = options.window || window;

    element.addEventListener('click', (event) => {
      let target = this.element.parentNode;
      while (!target.classList.contains("alert")) {
        target = target.parentNode;
      }
      target.remove();
    });
  }
}

module.exports = AlertCloseButtonController;
