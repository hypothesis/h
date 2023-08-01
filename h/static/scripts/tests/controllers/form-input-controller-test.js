import { FormInputController } from '../../controllers/form-input-controller';

import { setupComponent } from './util';

describe('FormInputController', () => {
  const template = `
    <div class="js-form-input">
      <label>Some label</label>
      <input type="text" name="some-text-input">
    </div>
  `.trim();

  it('does not set `hasError` state of controller if rendered without "is-error" class', () => {
    const ctrl = setupComponent(document, template, FormInputController);
    assert.equal(ctrl.state.hasError, false);
  });

  it('sets `hasError` state of controller if rendered with "is-error" class', () => {
    const errorTemplate = template.replace(
      'js-form-input',
      'js-form-input is-error',
    );
    const ctrl = setupComponent(document, errorTemplate, FormInputController);
    assert.equal(ctrl.state.hasError, true);
  });

  it('resets `hasError` state when an input event occurs', () => {
    const ctrl = setupComponent(document, template, FormInputController);
    const input = ctrl.element.querySelector('input');
    ctrl.setState({ hasError: true });

    input.dispatchEvent(new Event('input', { bubbles: true }));

    assert.equal(ctrl.state.hasError, false);
  });

  it('toggles "is-error" class when setting `hasError` state', () => {
    const ctrl = setupComponent(document, template, FormInputController);

    ctrl.setState({ hasError: true });
    assert.equal(ctrl.element.classList.contains('is-error'), true);

    ctrl.setState({ hasError: false });
    assert.equal(ctrl.element.classList.contains('is-error'), false);
  });
});
