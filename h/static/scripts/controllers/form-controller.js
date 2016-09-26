'use strict';

var Controller = require('../base/controller');
var { findRefs, setElementState } = require('../util/dom');
var modalFocus = require('../util/modal-focus');
var submitForm = require('../util/submit-form');

function shouldAutosubmit(type) {
  var autosubmitTypes = ['checkbox', 'radio'];
  return autosubmitTypes.indexOf(type) !== -1;
}

/**
 * Return true if a form field should be hidden until the user starts
 * editing the form.
 */
function isHiddenField(el) {
  return el.dataset.hideUntilActive;
}

/**
 * A controller which adds inline editing functionality to forms
 */
class FormController extends Controller {
  constructor(element, options) {
    super(element, options);

    setElementState(this.refs.cancelBtn, {hidden: false});
    this.refs.cancelBtn.addEventListener('click', event => {
      event.preventDefault();
      this.cancel();
    });

    // List of groups of controls that constitute each form field
    this._fields = Array.from(element.querySelectorAll('.js-form-input'))
      .map(el => {
        var parts = findRefs(el);
        return {
          container: el,
          input: parts.formInput,
          label: parts.label,
        };
      });

    this.on('focus', event => {
      var field = this._fields.find(field => field.input === event.target);
      if (!field) {
        return;
      }

      this.setState({
        editingFields: this._editSet(field),
        focusedField: field,
      });
    }, true /* capture - focus does not bubble */);

    this.on('change', event => {
      if (shouldAutosubmit(event.target.type)) {
        this.submit();
      }
    });

    this.on('input', event => {
      // Some but not all browsers deliver an `input` event for radio/checkbox
      // inputs. Since we auto-submit when such inputs change, don't mark the
      // field as dirty.
      if (shouldAutosubmit(event.target.type)) {
        return;
      }
      this.setState({dirty: true});
    });

    this.on('keydown', event => {
      event.stopPropagation();
      if (event.key === 'Escape') {
        this.cancel();
      }
    });

    // Ignore clicks outside of the active field when editing
    this.refs.formBackdrop.addEventListener('mousedown', event => {
      event.preventDefault();
      event.stopPropagation();
    });

    // Setup AJAX handling for forms
    this.on('submit', event => {
      event.preventDefault();
      this.submit();
    });

    this.setState({
      // True if the user has made changes to the field they are currently
      // editing
      dirty: false,
      // The set of fields currently being edited
      editingFields: [],
      // The field within the `editingFields` set that was last focused
      focusedField: null,
      // Markup for the original form. Used to revert the form to its original
      // state when the user cancels editing
      originalForm: this.element.outerHTML,
      // Flag that indicates a save is currently in progress
      saving: false,
      // Error that occurred while submitting the form
      submitError: '',
    });
  }

  update(state, prevState) {
    this._fields.forEach(field =>
      setElementState(field.container, {
        editing: state.editingFields.includes(field),
        focused: field === state.focusedField,
        hidden: isHiddenField(field.container) &&
                !state.editingFields.includes(field),
      })
    );

    // In forms that support editing a single field at a time, show the
    // Save/Cancel buttons below the field that we are currently editing.
    //
    // In the current forms that support editing multiple fields at once,
    // we always display the Save/Cancel buttons in their default position
    if (state.editingFields.length === 1) {
      state.editingFields[0].container.parentElement.insertBefore(
        this.refs.formActions,
        state.editingFields[0].container.nextSibling
      );
    }

    if (state.editingFields.length > 0 &&
        state.editingFields !== prevState.editingFields) {
      this._trapFocus();
    }

    var isEditing = state.editingFields.length > 0;
    setElementState(this.element, {editing: isEditing});
    setElementState(this.refs.formActions, {
      hidden: !isEditing || shouldAutosubmit(state.editingFields[0].input.type),
      saving: state.saving,
    });

    setElementState(this.refs.formSubmitError, {
      visible: state.submitError.length > 0,
    });
    this.refs.formSubmitErrorMessage.textContent = state.submitError;

    // Update fields depending on active/inactive state of the form
    this._fields.forEach(field => {
      // Fields may specify different labels for when the form is active vs
      // inactive.
      var activeLabel = field.container.dataset.activeLabel;
      var inactiveLabel = field.container.dataset.inactiveLabel;
      if (activeLabel && inactiveLabel) {
        field.label.textContent = isEditing ? activeLabel : inactiveLabel;
      }

      // The UA may or may not autofill password fields.
      // Set a dummy password as a placeholder when the field is not being edited
      // so that it appears non-empty if the UA doesn't autofill it.
      if (field.input.type === 'password') {
        field.input.setAttribute('placeholder', !isEditing ? '••••••••' : '');
      }
    });
  }

  beforeRemove() {
    if (this._releaseFocus) {
      this._releaseFocus();
    }
  }

  /**
   * Perform an AJAX submission of the form and replace it with the rendered
   * result.
   */
  submit() {
    var originalForm = this.state.originalForm;

    var activeInputId;
    if (this.state.editingFields.length > 0) {
      activeInputId = this.state.editingFields[0].input.id;
    }

    this.setState({saving: true});

    return submitForm(this.element).then(response => {
      this.options.reload(response.form);
    }).catch(err => {
      if (err.form) {
        // The server processed the request but rejected the submission.
        // Display the returned form which will contain any validation error
        // messages.
        var newFormEl = this.options.reload(err.form);
        var newFormCtrl = newFormEl.controllers.find(ctrl =>
          ctrl instanceof FormController);

        // Resume editing the field where validation failed
        var newInput = document.getElementById(activeInputId);
        if (newInput) {
          newInput.focus();
        }

        newFormCtrl.setState({
          // Mark the field in the replaced form as dirty since it has unsaved
          // changes
          dirty: newInput !== null,
          // If editing is canceled, revert back to the _original_ version of
          // the form, not the version with validation errors from the server.
          originalForm,
        });
      } else {
        // If there was an error processing the request or the server could
        // not be reached, display a helpful error
        this.setState({
          submitError: err.reason,
          saving: false,
        });
      }
    });
  }

  /**
   * Return the set of elements that the user should be able to interact with,
   * depending upon the field which is currently focused.
   */
  _focusGroup() {
    var fieldContainers = this.state.editingFields.map(field => field.container);
    if (fieldContainers.length === 0) {
      return null;
    }

    return [this.refs.formActions].concat(fieldContainers);
  }

  _trapFocus() {
    this._releaseFocus = modalFocus.trap(this._focusGroup(), newFocusedElement => {
      // Keep focus in the current field when it has unsaved changes,
      // otherwise let the user focus another field in the form or move focus
      // outside the form entirely.
      if (this.state.dirty) {
        return this.state.editingFields[0].input;
      }

      // If the user tabs out of the form, clear the editing state
      if (!this.element.contains(newFocusedElement)) {
        this.setState({editingFields: []});
      }

      return null;
    });
  }

  /**
   * Return the set of fields that should be displayed in the editing state
   * when a given field is selected.
   */
  _editSet(field) {
    // Currently we have two types of form:
    // 1. Forms which only edit one field at a time
    // 2. Forms with hidden fields (eg. the Change Email, Change Password forms)
    //    which should enable editing all fields when any is focused
    if (this._fields.some(field => isHiddenField(field.container))) {
      return this._fields;
    } else {
      return [field];
    }
  }

  /**
   * Cancel editing for the currently active field and revert any unsaved
   * changes.
   */
  cancel() {
    this.options.reload(this.state.originalForm);
  }
}

module.exports = FormController;
