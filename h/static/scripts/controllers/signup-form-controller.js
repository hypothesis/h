'use strict';

function SignupFormController(element) {
  var self = this;
  var form = element;

  this._submitBtn = element.querySelector('.js-signup-btn')

  form.addEventListener('submit', event => {
    this._submitBtn.disabled = true;
  });
}

module.exports = SignupFormController;
