'use strict';

var FormSelectOnFocusController = require('../controllers/form-select-onfocus-controller');

// helper to dispatch a native event to an element
function sendEvent(element, eventType) {
  // createEvent() used instead of Event constructor
  // for PhantomJS compatibility
  var event = document.createEvent('Event');
  event.initEvent(eventType, true /* bubbles */, true /* cancelable */);
  element.dispatchEvent(event);
}

describe('FormSelectOnFocusController', function() {
  var root;

  beforeEach(function() {
    root = document.createElement('div');
    root.innerHTML = '<form id="js-users-delete-form">' +
                     '<input type="text" class="js-select-onfocus" value="some-test-value">';
    document.body.appendChild(root);
  });

  afterEach(function() {
    root.parentNode.removeChild(root);
  });

  it('it selects the element on focus event', function() {
    new FormSelectOnFocusController(root);
    var input = root.querySelector('input');
    sendEvent(input, 'focus');
    assert.strictEqual(input.selectionStart, 0);
    assert.strictEqual(input.selectionEnd, input.value.length);
  });

  it('it selects the element without focus event when it is the active element', function() {
    // Focus element before instantiating the controller
    var input = root.querySelector('input');
    input.focus();

    new FormSelectOnFocusController(document.body);
    assert.strictEqual(input.selectionStart, 0);
    assert.strictEqual(input.selectionEnd, input.value.length);
  });
});
