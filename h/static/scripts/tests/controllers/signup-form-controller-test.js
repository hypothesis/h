'use strict';

var SignupFormController = require('../../controllers/signup-form-controller')

// helper to dispatch a native event to an element
function sendEvent(element, eventType) {
  // createEvent() used instead of Event constructor
  // for PhantomJS compatibility
  var event = document.createEvent('Event');
  event.initEvent(eventType, true /* bubbles */, true /* cancelable */);
  element.dispatchEvent(event);
}

describe('SignupFormController', function() {
  var element;
  var template;
  var form;
  var submitBtn;

  before(function () {
    template = '<form class="js-signup-form">' +
               '<input type="submit" class="js-signup-btn">' +
               '</form>'
  });

  beforeEach(function () {
    element = document.createElement('div');
    element.innerHTML = template;
    form = element.querySelector('.js-signup-form');
    submitBtn = element.querySelector('.js-signup-btn');
  });

  it('disables the submit button on form submit', function () {
    var controller = new SignupFormController(form);
    assert.isFalse(submitBtn.disabled);
    sendEvent(form, 'submit');
    assert.isTrue(submitBtn.disabled);
  });
});
