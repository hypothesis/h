'use strict';

var inherits = require('inherits');

var Controller = require('../base/controller');
var dom = require('../util/dom');
var submitForm = require('../util/submit-form');

var setElementState = dom.setElementState;

function container(el) {
  if (el.dataset.ref && el.dataset.ref.indexOf('formInputContainer') !== -1) {
    return el;
  } else {
    return container(el.parentElement);
  }
}

/**
 * A controller which adds inline editing functionality to forms
 */
function FormController(element) {
  Controller.call(this, element);

  this._init(element);
}
inherits(FormController, Controller);

FormController.prototype._init = function (element) {
  var self = this;

  var inlineEditingEnabled = !!element.dataset.inlineEditing;
  if (!inlineEditingEnabled) {
    setElementState(this.refs.formButtons, {visible: true});
    return;
  }

  setElementState(this.refs.cancelBtn, {hidden: false});
  this.refs.cancelBtn.addEventListener('click', function (event) {
    event.preventDefault();
    self.cancel();
  });
  element.addEventListener('keypress', function (event) {
    if (event.key === 'Escape') {
      self.cancel();
    }
  });

  // Begin editing when an input field is focused
  [].concat(this.refs.formInput).forEach(function (inputEl) {
    inputEl.addEventListener('focus', function () {
      if (self.state.editingField !== inputEl) {
        self.setState({
          editingField: inputEl,
          initialValue: inputEl.value,
        });
      }
    });
  });

  // Setup AJAX handling for forms
  element.addEventListener('submit', function (event) {
    event.preventDefault();
    self.submit();
  });

  this.state = {
    editing: false,
    saving: false,
  };
  this.update(this.state, {});
};

FormController.prototype.update = function (state, prevState) {
  if (prevState.editingField !== state.editingField) {
    if (prevState.editingField) {
      setElementState(container(prevState.editingField), {
        editing: false,

        // Hide validation error messages after reverting field to previous
        // value. The `error` state may be set on the server.
        error: false,
      });
      if (prevState.initialValue) {
        prevState.editingField.value = prevState.initialValue;
      }
      prevState.editingField.blur();
    }

    if (state.editingField) {
      state.editingField.focus();
      setElementState(container(state.editingField), {editing: true});
      state.editingField.parentElement.insertBefore(this.refs.formButtons,
        state.editingField.nextSibling);
    }
  }

  var isEditing = !!state.editingField;
  this.refs.formBackdrop.style.display = isEditing ? 'block' : 'none';

  setElementState(this.element, {editing: isEditing});
  setElementState(this.refs.formButtons, {
    visible: isEditing,
    saving: state.saving,
  });
};

/**
 * Cancel editing for the currently active field.
 */
FormController.prototype.cancel = function () {
  this.setState({editingField: null});
};

/**
 * Replace the form with an updated version rendered on the server.
 * @param {string} form
 */
FormController.prototype._reload = function (form) {
  this.reload(form);
  this._init(this.element);
};

/**
 * Perform an AJAX submission of the form and replace it with the rendered
 * result.
 */
FormController.prototype.submit = function () {
  this.setState({saving: true});

  var self = this;
  return submitForm(this.element).then(function (rsp) {
    self.setState({editingField: null});
    self._reload(rsp.form);

  }).catch(function (err) {
    var activeFieldId;
    var prevValue;
    if (self.state.editingField) {
      activeFieldId = self.state.editingField.id;
      prevValue = self.state.initialValue;
    }

    self._reload(err.form);

    // Resume editing the field.
    // TODO - When the user presses escape we need to revert the form back to
    // its saved state
    if (activeFieldId) {
      var failedField = document.getElementById(activeFieldId);
      self.setState({
        editingField: failedField,
        initialValue: prevValue,
      });
    }
  }).then(function () {
    self.setState({saving: false});
  });
};

module.exports = FormController;
