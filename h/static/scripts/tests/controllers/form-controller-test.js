import { upgradeElements } from '../../base/upgrade-elements';
import { FormController, $imports } from '../../controllers/form-controller';
import { hyphenate } from '../../util/string';

/**
 * Converts a map of data attribute names to string values into a string
 * containing equivalent data attributes.
 *
 * Note: This is not suitable for use outside tests, attribute values are not
 * escaped.
 *
 * eg. dataAttrs({activeLabel: 'label'}) => 'data-active-label="label"'
 */
function dataAttrs(data) {
  const dataAttrs = [];
  Object.keys(data || {}).forEach(key => {
    dataAttrs.push(`data-${hyphenate(key)}="${data[key]}"`);
  });
  return dataAttrs.join(' ');
}

// Simplified version of form fields rendered by deform on the server in
// mapping_item.jinja2
function fieldTemplate(field) {
  const dataAttr = dataAttrs(field.data);
  const typeAttr = field.type ? `type="${field.type}"` : '';

  return `<div class="js-form-input" data-ref="${field.fieldRef}" ${dataAttr}>
    <label data-ref="label ${field.labelRef}">Label</label>
    <input id="deformField" data-ref="formInput ${field.ref}" ${typeAttr} value="${field.value}">
  </div>`;
}

// Simplified version of forms rendered by deform on the server in form.jinja2
function formTemplate(fields) {
  return `
  <form class="js-form">
    <div data-ref="formBackdrop"></div>
    ${fields.map(fieldTemplate)}
    <div data-ref="formActions">
      <button data-ref="testSaveBtn">Save</button>
      <button data-ref="cancelBtn">Cancel</button>
    </div>
    <div data-ref="formSubmitError">
      <div data-ref="formSubmitErrorMessage"></div>
    </div>
  </form>
`;
}

const FORM_TEMPLATE = formTemplate([
  {
    ref: 'firstInput',
    value: 'original value',
  },
  {
    ref: 'secondInput',
    value: 'original value 2',
  },
  {
    ref: 'checkboxInput',
    type: 'checkbox',
  },
]);

const UPDATED_FORM = FORM_TEMPLATE.replace('js-form', 'js-form is-updated');

describe('FormController', () => {
  let ctrl;
  let fakeSubmitForm;
  let reloadSpy;

  function initForm(template) {
    fakeSubmitForm = sinon.stub();
    $imports.$mock({
      '../util/submit-form': { submitForm: fakeSubmitForm },
    });

    const container = document.createElement('div');
    container.innerHTML = template;
    upgradeElements(container, {
      '.js-form': FormController,
    });

    ctrl = container.querySelector('.js-form').controllers[0];

    // Wrap the original `reload` function passed to the controller so we can
    // spy on calls to it and update `ctrl` to the new controller instance
    // when the form is reloaded
    const reloadFn = ctrl.options.reload;
    reloadSpy = sinon.spy(html => {
      const newElement = reloadFn(html);
      ctrl = newElement.controllers[0];
      return newElement;
    });
    ctrl.options.reload = reloadSpy;

    // Add element to document so that it can be focused
    document.body.appendChild(ctrl.element);
  }

  beforeEach(() => {
    // Setup a form with the default template
    initForm(FORM_TEMPLATE);
  });

  afterEach(() => {
    ctrl.beforeRemove();
    ctrl.element.remove();
    $imports.$restore();
  });

  function isEditing() {
    return ctrl.element.classList.contains('is-editing');
  }

  function submitForm() {
    return ctrl.submit();
  }

  function startEditing() {
    ctrl.refs.firstInput.focus();
  }

  function isSaving() {
    return ctrl.refs.formActions.classList.contains('is-saving');
  }

  function submitError() {
    if (!ctrl.refs.formSubmitError.classList.contains('is-visible')) {
      return '<hidden>';
    }
    return ctrl.refs.formSubmitErrorMessage.textContent;
  }

  it('begins editing when a field is focused', () => {
    ctrl.refs.firstInput.focus();
    ctrl.refs.firstInput.dispatchEvent(new Event('focus'));
    assert.isTrue(isEditing());
  });

  it('reverts the form when "Cancel" is clicked', () => {
    startEditing();
    ctrl.refs.firstInput.value = 'new value';
    ctrl.refs.cancelBtn.click();
    assert.equal(ctrl.refs.firstInput.value, 'original value');
  });

  it('reverts the form when "Escape" key is pressed', () => {
    startEditing();
    const event = new Event('keydown', { bubbles: true });
    event.key = 'Escape';
    ctrl.refs.firstInput.dispatchEvent(event);
    assert.equal(ctrl.refs.firstInput.value, 'original value');
  });

  it('submits the form when "Save" is clicked', () => {
    fakeSubmitForm.returns(
      Promise.resolve({ status: 200, form: UPDATED_FORM }),
    );
    ctrl.refs.testSaveBtn.click();
    assert.calledWith(fakeSubmitForm, ctrl.element);

    // Ensure that test does not complete until `FormController#submit` has
    // run
    return Promise.resolve();
  });

  context('when form is successfully submitted', () => {
    it('updates form with new rendered version from server', () => {
      fakeSubmitForm.returns(
        Promise.resolve({ status: 200, form: UPDATED_FORM }),
      );
      return submitForm().then(() => {
        assert.isTrue(ctrl.element.classList.contains('is-updated'));
      });
    });

    it('stops editing the form', () => {
      fakeSubmitForm.returns(
        Promise.resolve({ status: 200, form: UPDATED_FORM }),
      );
      return submitForm().then(() => {
        assert.isFalse(isEditing());
      });
    });
  });

  context('when validation fails', () => {
    it('updates form with rendered version from server', () => {
      startEditing();
      fakeSubmitForm.returns(
        Promise.reject({ status: 400, form: UPDATED_FORM }),
      );
      return submitForm().then(() => {
        assert.isTrue(ctrl.element.classList.contains('is-updated'));
      });
    });

    it('marks updated form as dirty', () => {
      startEditing();
      fakeSubmitForm.returns(
        Promise.reject({ status: 400, form: UPDATED_FORM }),
      );
      return submitForm().then(() => {
        assert.isTrue(ctrl.state.dirty);
      });
    });

    it('continues editing current field', () => {
      startEditing();
      fakeSubmitForm.returns(
        Promise.reject({ status: 400, form: UPDATED_FORM }),
      );
      return submitForm().then(() => {
        assert.isTrue(isEditing());
      });
    });

    it('focuses the matching input field in the re-rendered form', () => {
      startEditing();
      fakeSubmitForm.returns(
        Promise.reject({ status: 400, form: UPDATED_FORM }),
      );

      // Simulate the user saving the form by clicking the 'Save' button, which
      // changes the focus from the input field to the button
      ctrl.refs.testSaveBtn.focus();

      return submitForm().then(() => {
        // In the re-rendered form, the input field should be focused
        assert.equal(document.activeElement.id, 'deformField');
      });
    });
  });

  it('enters the "saving" state while the form is being submitted', () => {
    fakeSubmitForm.returns(
      Promise.resolve({ status: 200, form: UPDATED_FORM }),
    );
    const saved = submitForm();
    assert.isTrue(isSaving());
    return saved.then(() => {
      assert.isFalse(isSaving());
    });
  });

  it('displays an error if form submission fails without returning a new form', () => {
    fakeSubmitForm.returns(
      Promise.reject({ status: 501, reason: 'Internal Server Error' }),
    );
    return submitForm().then(() => {
      assert.equal(submitError(), 'Internal Server Error');
    });
  });

  it('Displays a generic error message when an internal error occurs inside of submit form', () => {
    fakeSubmitForm.returns(Promise.reject(new Error('An internal issue')));
    return submitForm().then(() => {
      assert.equal(submitError(), 'There was a problem saving changes.');
    });
  });

  it('ignores clicks outside the field being edited', () => {
    startEditing();
    const event = new Event('mousedown', { cancelable: true });
    ctrl.refs.formBackdrop.dispatchEvent(event);
    assert.isTrue(event.defaultPrevented);
  });

  it('sets form state to dirty if user modifies active field', () => {
    startEditing();

    ctrl.refs.firstInput.dispatchEvent(new Event('input', { bubbles: true }));

    assert.isTrue(ctrl.state.dirty);
  });

  context('when focus moves to another input while editing', () => {
    it('clears editing state of first input', () => {
      startEditing();
      const inputs = ctrl.element.querySelectorAll('.js-form-input');

      // Focus second input. Although the user cannot focus the second input with
      // the mouse while the first is focused, they can navigate to it with the
      // tab key
      ctrl.refs.secondInput.focus();

      assert.isFalse(inputs[0].classList.contains('is-editing'));
      assert.isTrue(inputs[1].classList.contains('is-editing'));
    });

    it('keeps focus in previous input if it has unsaved changes', () => {
      startEditing();
      ctrl.setState({ dirty: true });

      // Simulate user/browser attempting to switch to another field
      ctrl.refs.secondInput.focus();

      assert.equal(document.activeElement, ctrl.refs.firstInput);
    });
  });

  context('when focus moves outside of form', () => {
    let outsideEl;

    beforeEach(() => {
      outsideEl = document.createElement('input');
      document.body.appendChild(outsideEl);
    });

    afterEach(() => {
      outsideEl.remove();
    });

    it('clears editing state if field does not have unsaved changes', () => {
      startEditing();

      // Simulate user moving focus outside of form (eg. via tab key).
      outsideEl.focus();

      assert.isFalse(isEditing());
    });

    it('keeps current field focused if it has unsaved changes', () => {
      startEditing();
      ctrl.setState({ dirty: true });

      // Simulate user/browser attempting to switch focus to an element outside
      // the form
      outsideEl.focus();

      assert.equal(document.activeElement, ctrl.refs.firstInput);
    });
  });

  context('when a checkbox is toggled', () => {
    beforeEach(() => {
      fakeSubmitForm.returns(
        Promise.resolve({ status: 200, form: UPDATED_FORM }),
      );
      ctrl.refs.checkboxInput.focus();
      ctrl.refs.checkboxInput.dispatchEvent(
        new Event('change', { bubbles: true }),
      );
    });

    afterEach(() => {
      // Wait for form submission to complete
      return Promise.resolve();
    });

    it('does not show form save buttons', () => {
      assert.isTrue(ctrl.refs.formActions.classList.contains('is-hidden'));
    });

    it('automatically submits the form', () => {
      assert.calledWith(fakeSubmitForm, ctrl.element);
    });
  });

  describe('forms with hidden fields', () => {
    beforeEach(() => {
      // Setup a form like the 'Change Email' which has a field that is initially
      // visible plus additional fields that are shown once the form is being
      // edited
      initForm(
        formTemplate([
          {
            fieldRef: 'emailContainer',
            ref: 'emailInput',
            value: 'jim@smith.com',
          },
          {
            fieldRef: 'passwordContainer',
            ref: 'passwordInput',
            value: '',
            type: 'password',
            data: {
              hideUntilActive: true,
            },
          },
        ]),
      );
    });

    function isConfirmFieldHidden() {
      return ctrl.refs.passwordContainer.classList.contains('is-hidden');
    }

    it('hides initially-hidden fields', () => {
      assert.isTrue(isConfirmFieldHidden());
    });

    it('shows initially-hidden fields when the email input is focused', () => {
      ctrl.refs.emailInput.focus();
      assert.isFalse(isConfirmFieldHidden());
    });

    it('hides initially-hidden fields when no input is focused', () => {
      const externalControl = document.createElement('input');
      document.body.appendChild(externalControl);

      ctrl.refs.emailInput.focus();
      externalControl.focus();

      assert.isTrue(isConfirmFieldHidden());
      externalControl.remove();
    });

    it('shows all fields in an editing state when any is focused', () => {
      const containers = [
        ctrl.refs.emailContainer,
        ctrl.refs.passwordContainer,
      ];
      const inputs = [ctrl.refs.emailInput, ctrl.refs.passwordInput];

      inputs.forEach(input => {
        input.focus();

        const editing = containers.filter(el =>
          el.classList.contains('is-editing'),
        );
        assert.equal(editing.length, 2);
      });
    });
  });

  describe('fields with inactive and active labels', () => {
    beforeEach(() => {
      initForm(
        formTemplate([
          {
            labelRef: 'passwordLabel',
            ref: 'passwordInput',
            type: 'password',
            data: {
              activeLabel: 'Current password',
              inactiveLabel: 'Password',
            },
          },
        ]),
      );
    });

    it('uses the inactive label for fields when the form is inactive', () => {
      assert.equal(ctrl.refs.passwordLabel.textContent, 'Password');
    });

    it('uses the active label for fields when the form is active', () => {
      ctrl.refs.passwordInput.focus();
      assert.equal(ctrl.refs.passwordLabel.textContent, 'Current password');
    });
  });

  describe('password fields', () => {
    beforeEach(() => {
      initForm(
        formTemplate([
          {
            ref: 'password',
            type: 'password',
          },
        ]),
      );
    });

    it('adds a placeholder to inactive password fields', () => {
      assert.equal(ctrl.refs.password.getAttribute('placeholder'), '••••••••');
    });

    it('clears the placeholder when the password field is focused', () => {
      ctrl.refs.password.focus();
      assert.equal(ctrl.refs.password.getAttribute('placeholder'), '');
    });
  });
});
