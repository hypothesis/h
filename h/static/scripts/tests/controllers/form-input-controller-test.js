'use strict';

const FormInputController = require('../../controllers/form-input-controller');

const { setupComponent } = require('./util');

describe('FormInputController', () => {
  const template = `
    <div class="js-form-input">
      <label>Some label</label>
      <input type="text" data-ref="formInput">
    </div>
  `.trim();

  it('does not set `hasError` state of controller if rendered without "is-error" class', () => {
    const ctrl = setupComponent(document, template, FormInputController);
    assert.equal(ctrl.state.hasError, false);
  });

  it('sets `hasError` state of controller if rendered with "is-error" class', () => {
    const errorTemplate = template.replace('js-form-input', 'js-form-input is-error');
    const ctrl = setupComponent(document, errorTemplate, FormInputController);
    assert.equal(ctrl.state.hasError, true);
  });

  it('toggles "is-error" class when setting `hasError` state', () => {
    const ctrl = setupComponent(document, template, FormInputController);

    ctrl.setState({ hasError: true });
    assert.equal(ctrl.element.classList.contains('is-error'), true);

    ctrl.setState({ hasError: false });
    assert.equal(ctrl.element.classList.contains('is-error'), false);
  });
});
