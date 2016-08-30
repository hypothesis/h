'use strict';

var proxyquire = require('proxyquire');

var util = require('./util');
var noCallThru = require('../util').noCallThru;

// Simplified version of forms rendered by deform, with the `js-` hooks expected
// by the controller
var TEMPLATE = [
  '<form class="js-form" data-inline-editing="true">',
  '<div data-ref="formBackdrop"></div>',
  '<div data-ref="formInputContainer">',
  '<input id="deformField" data-ref="formInput">',
  '</div>',
  '<div data-ref="formButtons">',
  '<button data-ref="testSaveBtn">Save</button><button data-ref="cancelBtn">',
  '</div>',
  '</form>',
].join('\n');

var UPDATED_FORM = TEMPLATE.replace('js-form', 'js-form is-updated');

describe('FormController', function () {
  var ctrl;
  var fakeSubmitForm;

  beforeEach(function () {
    fakeSubmitForm = sinon.stub();
    var FormController = proxyquire('../../controllers/form-controller', {
      '../util/submit-form': noCallThru(fakeSubmitForm),
    });

    ctrl = util.setupComponent(document, TEMPLATE, FormController);
  });

  afterEach(function () {
    ctrl.element.remove();
  });

  function isEditing() {
    return ctrl.element.classList.contains('is-editing');
  }

  function submitForm() {
    return ctrl.submit();
  }

  function startEditing() {
    ctrl.refs.formInput.focus();
    ctrl.refs.formInput.dispatchEvent(new Event('focus'));
  }

  function isSaving() {
    return ctrl.refs.formButtons.classList.contains('is-saving');
  }

  it('begins editing when a field is focused', function () {
    ctrl.refs.formInput.focus();
    ctrl.refs.formInput.dispatchEvent(new Event('focus'));
    assert.isTrue(isEditing());
  });

  it('shows backdrop when editing a field', function () {
    startEditing();
    assert.equal(ctrl.refs.formBackdrop.style.display, 'block');
  });

  it('cancels editing when "Cancel" is clicked', function () {
    startEditing();
    ctrl.refs.cancelBtn.click();
    assert.isFalse(isEditing());
  });

  it('cancels editing when "Escape" is pressed', function () {
    startEditing();
    var event = new Event('keypress');
    event.key = 'Escape';
    ctrl.element.dispatchEvent(event);
    assert.isFalse(isEditing());
  });

  it('reverts a field to its previous value when editing is canceled', function () {
    ctrl.refs.formInput.value = 'old value';
    startEditing();
    ctrl.refs.formInput.value = 'new value';
    ctrl.refs.cancelBtn.click();
    assert.equal(ctrl.refs.formInput.value, 'old value');
  });

  it('hides validation errors when editing is canceled', function () {
    startEditing();

    // Simulate `error` state being set on field, usually as a result of
    // the server setting a validation error message
    ctrl.refs.formInputContainer.classList.add('is-error');
    ctrl.refs.cancelBtn.click();
    assert.isFalse(ctrl.refs.formInputContainer.classList.contains('is-error'));
  });

  it('submits the form when "Save" is clicked', function () {
    fakeSubmitForm.returns(Promise.resolve({status: 200, form: UPDATED_FORM}));
    ctrl.refs.testSaveBtn.click();
    assert.calledWith(fakeSubmitForm, ctrl.element);

    // Ensure that test does not complete until `FormController#submit` has
    // run
    return Promise.resolve();
  });

  it('updates form with rendered version from server when the form is saved', function () {
    fakeSubmitForm.returns(Promise.resolve({status: 200, form: UPDATED_FORM}));
    return submitForm().then(function () {
      assert.isTrue(ctrl.element.classList.contains('is-updated'));
    });
  });

  it('stops editing the form when saving succeeds', function () {
    fakeSubmitForm.returns(Promise.resolve({status: 200, form: UPDATED_FORM}));
    return submitForm().then(function () {
      assert.isFalse(isEditing());
    });
  });

  it('updates form with rendered version from server when saving fails', function () {
    startEditing();
    fakeSubmitForm.returns(Promise.reject({status: 400, form: UPDATED_FORM}));
    return submitForm().then(function () {
      assert.isTrue(ctrl.element.classList.contains('is-updated'));
    });
  });

  it('keeps editing the form when saving fails', function () {
    startEditing();
    fakeSubmitForm.returns(Promise.reject({status: 400, form: UPDATED_FORM}));
    return submitForm().then(function () {
      assert.isTrue(isEditing());
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
});
