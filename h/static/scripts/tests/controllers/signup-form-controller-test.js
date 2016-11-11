'use strict';

var SignupFormController = require('../../controllers/signup-form-controller');

var TEMPLATE = `
  <form class="js-signup-form">
    <input type="submit" class="js-signup-btn">
  </form>
  `;

describe('SignupFormController', () => {
  var element;
  var form;
  var submitBtn;

  beforeEach(() => {
    element = document.createElement('div');
    element.innerHTML = TEMPLATE;
    form = element.querySelector('.js-signup-form');
    submitBtn = element.querySelector('.js-signup-btn');
  });

  it('disables the submit button on form submit', () => {
    new SignupFormController(form);
    assert.isFalse(submitBtn.disabled);
    form.dispatchEvent(new Event('submit'));
    assert.isTrue(submitBtn.disabled);
  });
});
