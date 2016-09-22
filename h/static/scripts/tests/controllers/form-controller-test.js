'use strict';

var proxyquire = require('proxyquire');

var { noCallThru } = require('../util');
var upgradeElements = require('../../base/upgrade-elements');

// Simplified version of form fields rendered by deform on the server in
// mapping_item.jinja2
function fieldTemplate(field) {
  var hideAttr = field.hide ? 'data-hide-until-active="true"' : '';
  var typeAttr = field.type ? `type="${field.type}"`;

  return `<div class="js-form-input" data-ref="${field.fieldRef}" ${hideAttr}>
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

var FORM_TEMPLATE = formTemplate([{
  ref: 'firstInput',
  value: 'original value',
},{
  ref: 'secondInput',
  value: 'original value 2',
},{
  ref: 'checkboxInput',
  type: 'checkbox',
}]);

var UPDATED_FORM = FORM_TEMPLATE.replace('js-form', 'js-form is-updated');

describe('FormController', function () {
  var ctrl;
  var fakeSubmitForm;
  var reloadSpy;

  function initForm(template) {
    fakeSubmitForm = sinon.stub();
    var FormController = proxyquire('../../controllers/form-controller', {
      '../util/submit-form': noCallThru(fakeSubmitForm),
    });

    var container = document.createElement('div');
    container.innerHTML = template;
    upgradeElements(container, {
      '.js-form': FormController,
    });

    ctrl = container.querySelector('.js-form').controllers[0];

    // Wrap the original `reload` function passed to the controller so we can
    // spy on calls to it and update `ctrl` to the new controller instance
    // when the form is reloaded
    var reloadFn = ctrl.options.reload;
    reloadSpy = sinon.spy(html => {
      var newElement = reloadFn(html);
      ctrl = newElement.controllers[0];
      return newElement;
    });
    ctrl.options.reload = reloadSpy;

    // Add element to document so that it can be focused
    document.body.appendChild(ctrl.element);
  }

  beforeEach(function () {
    // Setup a form with the default template
    initForm(FORM_TEMPLATE);
  });

  afterEach(function () {
    ctrl.beforeRemove();
    ctrl.element.remove();
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

  it('begins editing when a field is focused', function () {
    ctrl.refs.firstInput.focus();
    ctrl.refs.firstInput.dispatchEvent(new Event('focus'));
    assert.isTrue(isEditing());
  });

  it('reverts the form when "Cancel" is clicked', function () {
    startEditing();
    ctrl.refs.firstInput.value = 'new value';
    ctrl.refs.cancelBtn.click();
    assert.equal(ctrl.refs.firstInput.value, 'original value');
  });

  it('reverts the form when "Escape" key is pressed', function () {
    startEditing();
    var event = new Event('keydown', {bubbles: true});
    event.key = 'Escape';
    ctrl.refs.firstInput.dispatchEvent(event);
    assert.equal(ctrl.refs.firstInput.value, 'original value');
  });

  it('submits the form when "Save" is clicked', function () {
    fakeSubmitForm.returns(Promise.resolve({status: 200, form: UPDATED_FORM}));
    ctrl.refs.testSaveBtn.click();
    assert.calledWith(fakeSubmitForm, ctrl.element);

    // Ensure that test does not complete until `FormController#submit` has
    // run
    return Promise.resolve();
  });

  context('when form is successfully submitted', function () {
    it('updates form with new rendered version from server', function () {
      fakeSubmitForm.returns(Promise.resolve({status: 200, form: UPDATED_FORM}));
      return submitForm().then(function () {
        assert.isTrue(ctrl.element.classList.contains('is-updated'));
      });
    });

    it('stops editing the form', function () {
      fakeSubmitForm.returns(Promise.resolve({status: 200, form: UPDATED_FORM}));
      return submitForm().then(function () {
        assert.isFalse(isEditing());
      });
    });
  });

  context('when validation fails', function () {
    it('updates form with rendered version from server', function () {
      startEditing();
      fakeSubmitForm.returns(Promise.reject({status: 400, form: UPDATED_FORM}));
      return submitForm().then(function () {
        assert.isTrue(ctrl.element.classList.contains('is-updated'));
      });
    });

    it('marks updated form as dirty', function () {
      startEditing();
      fakeSubmitForm.returns(Promise.reject({status: 400, form: UPDATED_FORM}));
      return submitForm().then(function () {
        assert.isTrue(ctrl.state.dirty);
      });
    });

    it('continues editing current field', function () {
      startEditing();
      fakeSubmitForm.returns(Promise.reject({status: 400, form: UPDATED_FORM}));
      return submitForm().then(function () {
        assert.isTrue(isEditing());
      });
    });

    it('focuses the matching input field in the re-rendered form', function () {
      startEditing();
      fakeSubmitForm.returns(Promise.reject({status: 400, form: UPDATED_FORM}));

      // Simulate the user saving the form by clicking the 'Save' button, which
      // changes the focus from the input field to the button
      ctrl.refs.testSaveBtn.focus();

      return submitForm().then(function () {
        // In the re-rendered form, the input field should be focused
        assert.equal(document.activeElement.id, 'deformField');
      });
    });
  });

  it('enters the "saving" state while the form is being submitted', function () {
    fakeSubmitForm.returns(Promise.resolve({status: 200, form: UPDATED_FORM}));
    var saved = submitForm();
    assert.isTrue(isSaving());
    return saved.then(function () {
      assert.isFalse(isSaving());
    });
  });

  it('displays an error if form submission fails without returning a new form', function () {
    fakeSubmitForm.returns(Promise.reject({status: 500, reason: 'Internal Server Error'}));
    return submitForm().then(function () {
      assert.equal(submitError(), 'Internal Server Error');
    });
  });

  it('ignores clicks outside the field being edited', function () {
    startEditing();
    var event = new Event('mousedown', {cancelable: true});
    ctrl.refs.formBackdrop.dispatchEvent(event);
    assert.isTrue(event.defaultPrevented);
  });

  it('sets form state to dirty if user modifies active field', function () {
    startEditing();

    ctrl.refs.firstInput.dispatchEvent(new Event('input', {bubbles: true}));

    assert.isTrue(ctrl.state.dirty);
  });

  context('when focus moves to another input while editing', function () {
    it('clears editing state of first input', function () {
      startEditing();
      var inputs = ctrl.element.querySelectorAll('.js-form-input');

      // Focus second input. Although the user cannot focus the second input with
      // the mouse while the first is focused, they can navigate to it with the
      // tab key
      ctrl.refs.secondInput.focus();

      assert.isFalse(inputs[0].classList.contains('is-editing'));
      assert.isTrue(inputs[1].classList.contains('is-editing'));
    });

    it('keeps focus in previous input if it has unsaved changes', function () {
      startEditing();
      ctrl.setState({dirty: true});

      // Simulate user/browser attempting to switch to another field
      ctrl.refs.secondInput.focus();

      assert.equal(document.activeElement, ctrl.refs.firstInput);
    });
  });

  context('when focus moves outside of form', function () {
    var outsideEl;

    beforeEach(function () {
      outsideEl = document.createElement('input');
      document.body.appendChild(outsideEl);
    });

    afterEach(function () {
      outsideEl.remove();
    });

    it('clears editing state if field does not have unsaved changes', function () {
      startEditing();

      // Simulate user moving focus outside of form (eg. via tab key).
      outsideEl.focus();

      assert.isFalse(isEditing());
    });

    it('keeps current field focused if it has unsaved changes', function () {
      startEditing();
      ctrl.setState({dirty: true});

      // Simulate user/browser attempting to switch focus to an element outside
      // the form
      outsideEl.focus();

      assert.equal(document.activeElement, ctrl.refs.firstInput);
    });
  });

  context('when a checkbox is toggled', function () {
    beforeEach(function () {
      fakeSubmitForm.returns(Promise.resolve({status: 200, form: UPDATED_FORM}));
      ctrl.refs.checkboxInput.focus();
      ctrl.refs.checkboxInput.dispatchEvent(new Event('change', {bubbles: true}));
    });

    afterEach(function () {
      // Wait for form submission to complete
      return Promise.resolve();
    });

    it('does not show form save buttons', function () {
      assert.isTrue(ctrl.refs.formActions.classList.contains('is-hidden'));
    });

    it('automatically submits the form', function () {
      assert.calledWith(fakeSubmitForm, ctrl.element);
    });
  });

  context('when the form is a "Change Email"-type form', function () {
    beforeEach(function () {
      // Setup a form like the 'Change Email' or 'Change Password' form which
      // has a set of fields that are initially visible which trigger editing
      // plus a set of hidden fields that are shown once the user starts editing
      // the form
      initForm(formTemplate([{
        fieldRef: 'emailContainer',
        ref: 'emailInput',
        value: 'jim@smith.com',
      },{
        fieldRef: 'confirmPasswordContainer',
        ref: 'confirmPasswordInput',
        value: '',
        hide: true, // Only show this field when the user focuses the form
      }]));
    });

    function isConfirmFieldHidden() {
      return ctrl.refs.confirmPasswordContainer.classList.contains('is-hidden');
    }

    it('hides initially-hidden fields', function () {
      assert.isTrue(isConfirmFieldHidden());
    });

    it('shows initially-hidden fields when the email input is focused', function () {
      ctrl.refs.emailInput.focus();
      assert.isFalse(isConfirmFieldHidden());
    });

    it('hides initially-hidden fields when no input is focused', function () {
      var externalControl = document.createElement('input');
      document.body.appendChild(externalControl);

      ctrl.refs.emailInput.focus();
      externalControl.focus();

      assert.isTrue(isConfirmFieldHidden());
      externalControl.remove();
    });

    it('shows all fields in an editing state when any is focused', function () {
      var containers = [ctrl.refs.emailContainer, ctrl.refs.confirmPasswordContainer];
      var inputs = [ctrl.refs.emailInput, ctrl.refs.confirmPasswordInput];

      inputs.forEach(input => {
        input.focus();

        var editing = containers.filter(el => el.classList.contains('is-editing'));
        assert.equal(editing.length, 2);
      });
    });
  });
});
