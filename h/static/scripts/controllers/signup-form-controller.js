'use strict';

var Controller = require('../base/controller');

class SignupFormController extends Controller {
  constructor(element) {
    super(element);

    var submitBtn = element.querySelector('.js-signup-btn');

    element.addEventListener('submit', () => {
      submitBtn.disabled = true;
    });
  }
}

module.exports = SignupFormController;
