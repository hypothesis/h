'use strict';

const Controller = require('../base/controller');
const { setElementState } = require('../util/dom');

/**
 * Controller for individual form input fields.
 *
 * This is used for both forms with inline editing (ie. those which show "Save"
 * and "Cancel" buttons beneath individual form fields, see `FormController`)
 * and those without.
 *
 * Note that for forms using inline editing much of the logic lives in the
 * form-level controller rather than here.
 */
class FormInputController extends Controller {
  constructor(element) {
    super(element);

    const hasError = element.classList.contains('is-error');
    this.setState({ hasError });

    element.addEventListener('input', () => {
      this.setState({ hasError: false });
    });
  }

  update() {
    setElementState(this.element, { error: this.state.hasError });
  }
}

module.exports = FormInputController;
