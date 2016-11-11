'use strict';

const FormSelectOnFocusController = require('../../controllers/form-select-onfocus-controller');

// helper to dispatch a native event to an element
function sendEvent(element, eventType) {
  // createEvent() used instead of Event constructor
  // for PhantomJS compatibility
  const event = document.createEvent('Event');
  event.initEvent(eventType, true /* bubbles */, true /* cancelable */);
  element.dispatchEvent(event);
}

describe('FormSelectOnFocusController', () => {
  let root;

  beforeEach(() => {
    root = document.createElement('div');
    root.innerHTML = '<form id="js-users-delete-form">' +
                     '<input type="text" class="js-select-onfocus" value="some-test-value">';
    document.body.appendChild(root);
  });

  afterEach(() => {
    root.parentNode.removeChild(root);
  });

  it('it selects the element on focus event', () => {
    new FormSelectOnFocusController(root);
    const input = root.querySelector('input');
    sendEvent(input, 'focus');
    assert.strictEqual(input.selectionStart, 0);
    assert.strictEqual(input.selectionEnd, input.value.length);
  });

  it('it selects the element without focus event when it is the active element', () => {
    // Focus element before instantiating the controller
    const input = root.querySelector('input');
    input.focus();

    new FormSelectOnFocusController(document.body);
    assert.strictEqual(input.selectionStart, 0);
    assert.strictEqual(input.selectionEnd, input.value.length);
  });
});
