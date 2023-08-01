import { Controller } from '../base/controller';
import { findRefs, setElementState } from '../util/dom';
import * as modalFocus from '../util/modal-focus';
import { submitForm } from '../util/submit-form';

function shouldAutosubmit(type) {
  const autosubmitTypes = ['checkbox', 'radio'];
  return autosubmitTypes.indexOf(type) !== -1;
}

/**
 * Return true if a form field should be hidden until the user starts editing
 * the form.
 *
 * @param {Element} el - The container for an individual form field, which may
 *        have a "data-hide-until-active" attribute.
 */
function isHiddenField(el) {
  return el.dataset.hideUntilActive;
}

/**
 * @typedef {Object} Field
 * @property {Element} container - The container element for an input field
 * @property {HTMLInputElement} input - The <input> element for an input field
 * @property {HTMLLabelElement} label - The <label> element for a field
 */

/**
 * A controller which adds inline editing functionality to forms.
 *
 * When forms have inline editing enabled, individual fields can be edited and
 * changes can be saved without a full page reload.
 *
 * Instead when the user focuses a field, Save/Cancel buttons are shown beneath
 * the field and everything else on the page is dimmed. When the user clicks 'Save'
 * the form is submitted to the server via a `fetch()` request and the HTML of
 * the form is updated with the result, which may be a successfully updated form
 * or a re-rendered version of the form with validation errors indicated.
 */
export class FormController extends Controller {
  constructor(element, options) {
    super(element, options);

    setElementState(this.refs.cancelBtn, { hidden: false });
    this.refs.cancelBtn.addEventListener('click', event => {
      event.preventDefault();
      this.cancel();
    });

    // List of groups of controls that constitute each form field
    this._fields = Array.from(element.querySelectorAll('.js-form-input')).map(
      el => {
        const parts = findRefs(el);
        return {
          container: el,
          input: parts.formInput,
          label: parts.label,
        };
      },
    );

    this.on(
      'focus',
      event => {
        const field = this._fields.find(field => field.input === event.target);
        if (!field) {
          return;
        }

        this.setState({
          editingFields: this._editSet(field),
          focusedField: field,
        });
      },
      true /* capture - focus does not bubble */,
    );

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
      this.setState({ dirty: true });
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
    // In forms that support editing a single field at a time, show the
    // Save/Cancel buttons below the field that we are currently editing.
    //
    // In the current forms that support editing multiple fields at once,
    // we always display the Save/Cancel buttons in their default position
    if (state.editingFields.length === 1) {
      state.editingFields[0].container.parentElement.insertBefore(
        this.refs.formActions,
        state.editingFields[0].container.nextSibling,
      );
    }

    if (
      state.editingFields.length > 0 &&
      state.editingFields !== prevState.editingFields
    ) {
      this._trapFocus();
    }

    const isEditing = state.editingFields.length > 0;
    setElementState(this.element, { editing: isEditing });
    setElementState(this.refs.formActions, {
      hidden: !isEditing || shouldAutosubmit(state.editingFields[0].input.type),
      saving: state.saving,
    });

    setElementState(this.refs.formSubmitError, {
      visible: state.submitError.length > 0,
    });
    this.refs.formSubmitErrorMessage.textContent = state.submitError;

    this._updateFields(state);
  }

  /**
   * Update the appearance of individual form fields to match the current state
   * of the form.
   *
   * @param {Object} state - The internal state of the form
   */
  _updateFields(state) {
    this._fields.forEach(field => {
      setElementState(field.container, {
        editing: state.editingFields.includes(field),
        focused: field === state.focusedField,
        hidden:
          isHiddenField(field.container) &&
          !state.editingFields.includes(field),
      });

      // Update labels
      const activeLabel = field.container.dataset.activeLabel;
      const inactiveLabel = field.container.dataset.inactiveLabel;
      const isEditing = state.editingFields.includes(field);

      if (activeLabel && inactiveLabel) {
        field.label.textContent = isEditing ? activeLabel : inactiveLabel;
      }

      // Update placeholder
      //
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
    const originalForm = this.state.originalForm;

    let activeInputId;
    if (this.state.editingFields.length > 0) {
      activeInputId = this.state.editingFields[0].input.id;
    }

    this.setState({ saving: true });

    return submitForm(this.element)
      .then(response => {
        this.options.reload(response.form);
      })
      .catch(err => {
        if (err.form) {
          // The server processed the request but rejected the submission.
          // Display the returned form which will contain any validation error
          // messages.
          const newFormEl = this.options.reload(err.form);
          const newFormCtrl = newFormEl.controllers.find(
            ctrl => ctrl instanceof FormController,
          );

          // Resume editing the field where validation failed
          const newInput = document.getElementById(activeInputId);
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
            submitError: err.reason || 'There was a problem saving changes.',
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
    const fieldContainers = this.state.editingFields.map(
      field => field.container,
    );
    if (fieldContainers.length === 0) {
      return null;
    }

    return [this.refs.formActions].concat(fieldContainers);
  }

  /**
   * Trap focus within the set of form fields currently being edited.
   */
  _trapFocus() {
    this._releaseFocus = modalFocus.trap(
      this._focusGroup(),
      newFocusedElement => {
        // Keep focus in the current field when it has unsaved changes,
        // otherwise let the user focus another field in the form or move focus
        // outside the form entirely.
        if (this.state.dirty) {
          return this.state.editingFields[0].input;
        }

        // If the user tabs out of the form, clear the editing state
        if (!this.element.contains(newFocusedElement)) {
          this.setState({ editingFields: [] });
        }

        return null;
      },
    );
  }

  /**
   * Return the set of fields that should be displayed in the editing state
   * when a given field is selected.
   *
   * @param {Field} - The field that was focused
   * @return {Field[]} - Set of fields that should be active for editing
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
