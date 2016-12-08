'use strict';

const InputAutofocusController = require('../../controllers/input-autofocus-controller');
const { setupComponent } = require('./util');

/**
 * Send a 'keydown' event to the active element.
 *
 * @param {string} key - The key name value for the KeyboardEvent#key property.
 * @param {object} opts - Options for the keyboard event
 */
function sendKey(key, opts = {}) {
  // Note: PhantomJS 2.x does not support the KeyboardEvent constructor
  const event = new Event('keydown', {bubbles: true});
  event.key = key;
  Object.assign(event, opts);
  document.activeElement.dispatchEvent(event);
}

describe('InputAutofocusController', () => {
  let ctrl;
  let otherInput;

  before(() => {
    otherInput = document.createElement('input');
    document.body.appendChild(otherInput);
  });

  after(() => {
    otherInput.remove();
  });

  beforeEach(() => {
    const template = '<input>';
    ctrl = setupComponent(document, template, InputAutofocusController);
  });

  afterEach(() => {
    ctrl.beforeRemove();
  });

  context('when no other element has focus', () => {
    beforeEach(() => {
      if (document.activeElement !== document.body) {
        document.activeElement.blur();
        assert.equal(document.activeElement, document.body);
      }
    });

    it('should focus the input if a letter key is pressed', () => {
      sendKey('a');
      assert.equal(document.activeElement, ctrl.element);
    });

    it('should focus the input if Backspace is pressed', () => {
      sendKey('Backspace');
      assert.equal(document.activeElement, ctrl.element);
    });

    it('should not focus the input if a non-letter key is pressed', () => {
      sendKey('Enter');
      assert.notEqual(document.activeElement, ctrl.element);
    });

    it('should not focus the input if a letter key is pressed with a modifier', () => {
      sendKey('a', {ctrlKey: true});
      sendKey('b', {altKey: true});
      sendKey('c', {metaKey: true});
      assert.notEqual(document.activeElement, ctrl.element);
    });
  });

  context('when another element has focus', () => {
    beforeEach(() => {
      otherInput.focus();
    });

    it('should not focus the input if a letter key is pressed', () => {
      sendKey('a');
      assert.notEqual(document.activeElement, ctrl.element);
    });
  });

  context('when the input has focus', () => {
    beforeEach(() => {
      ctrl.element.focus();
    });

    it('should blur the input if the Escape key is pressed', () => {
      sendKey('Escape');
      assert.notEqual(document.activeElement, ctrl.element);
    });
  });
});
