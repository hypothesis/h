'use strict';

var Controller = require('../base/controller');
var { findRefs, setElementState } = require('../util/dom');
var submitForm = require('../util/submit-form');

function shouldAutosubmit(type) {
  var autosubmitTypes = ['checkbox', 'radio'];
  return autosubmitTypes.indexOf(type) !== -1;
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
        return {container: el, input: parts.formInput};
      });

    this.on('focus', event => {
      var field = this._fields.find(field => field.input === event.target);
      if (!field) {
        return;
      }

      // Enforce that the current field retains focus while it has unsaved
      // changes
      if (this.state.dirty &&
          this.state.editingField &&
          this.state.editingField !== field) {
        this.state.editingField.input.focus();
        return;
      }

      this.setState({editingField: field});
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

    // When the user tabs outside of the form, cancel editing
    this.on('blur', () => {
      // Add a timeout because `document.activeElement` is not updated until
      // after the event is processed
      setTimeout(() => {
        // If the user has made changes to the active element, then keep focus
        // on the active field, otherwise allow them to move to the previous /
        // next fields by tabbing
        if (this.state.dirty && !this._isEditingFieldFocused()) {
          this.state.editingField.input.focus();
        } else if (!this.element.contains(document.activeElement)) {
          this.setState({editingField: null});
        }
      }, 0);
    }, true /* capture - 'blur' does not bubble */);

    // Setup AJAX handling for forms
    this.on('submit', event => {
      event.preventDefault();
      this.submit();
    });

    this.setState({
      // True if the user has made changes to the field they are currently
      // editing
      dirty: false,
      // The group of elements (container, input) for the form field currently
      // being edited
      editingField: null,
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
    if (prevState.editingField &&
        state.editingField !== prevState.editingField) {
      setElementState(prevState.editingField.container, {editing: false});
    }

    if (state.editingField) {
      // Display Save/Cancel buttons below the field that we are currently
      // editing
      state.editingField.container.parentElement.insertBefore(
        this.refs.formActions,
        state.editingField.container.nextSibling
      );
      setElementState(state.editingField.container, {editing: true});
    }

    var isEditing = !!state.editingField;
    setElementState(this.element, {editing: isEditing});
    setElementState(this.refs.formActions, {
      hidden: !isEditing || shouldAutosubmit(state.editingField.input.type),
      saving: state.saving,
    });
    setElementState(this.refs.formSubmitError, {
      visible: state.submitError.length > 0,
    });
    this.refs.formSubmitErrorMessage.textContent = state.submitError;
  }

  /**
   * Perform an AJAX submission of the form and replace it with the rendered
   * result.
   */
  submit() {
    var originalForm = this.state.originalForm;

    var activeInputId;
    if (this.state.editingField) {
      activeInputId = this.state.editingField.input.id;
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
   * Return true if the field that the user last started editing currently has
   * focus.
   */
  _isEditingFieldFocused() {
    if (!this.state.editingField) {
      return false;
    }

    var focusedEl = document.activeElement;
    if (this.refs.formActions.contains(focusedEl)) {
      return true;
    }
    return this.state.editingField.container.contains(focusedEl);
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
