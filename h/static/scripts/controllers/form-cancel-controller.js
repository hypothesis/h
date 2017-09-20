'use strict';

const Controller = require('../base/controller');

/**
 * Button for canceling a form in a single-form page.
 *
 * This is used only when the form is *not* using inline editing.
 * Forms which use inline editing have a cancel button that is shown below the
 * active field. That is managed by `FormController`.
 */
class FormCancelController extends Controller {
  constructor(element, options) {
    super(element, options);

    const window_ = options.window || window;

    element.addEventListener('click', (event) => {
      event.preventDefault();
      window_.close();
    });
  }
}

module.exports = FormCancelController;
