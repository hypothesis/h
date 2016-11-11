'use strict';

const CharacterLimitController = require('../../controllers/character-limit-controller');
const util = require('./util');

describe('CharacterLimitController', () => {

  let ctrl;

  afterEach(() => {
    if (ctrl) {
      ctrl.element.remove();
      ctrl = null;
    }
  });

  /**
   * Make a <textarea> with the character limit controller enhancement
   * applied and return the various parts of the component.
   */
  function component(value, maxlength) {
    maxlength = maxlength || 250;

    let template = '<div class="js-character-limit">';
    template += '<textarea data-ref="characterLimitInput" data-maxlength="' + maxlength + '">';
    if (value) {
      template += value;
    }
    template += '</textarea><span data-ref="characterLimitCounter">Foo</span>';
    template += '</div>';

    ctrl = util.setupComponent(document, template, CharacterLimitController);

    return {
      counterEl: ctrl.refs.characterLimitCounter,
      textarea: ctrl.refs.characterLimitInput,
      ctrl: ctrl,
    };
  }

  it('adds the ready class', () => {
    const counterEl = component().counterEl;

    assert.equal(counterEl.classList.contains('is-ready'), true);
  });

  it('shows the counter initially even if textarea empty', () => {
    const counterEl = component().counterEl;

    assert.equal(counterEl.innerHTML, '0/250');
  });

  it('shows the counter if the element has pre-rendered text', () => {
    const counterEl = component('pre-rendered').counterEl;

    assert.equal(counterEl.innerHTML, '12/250');
  });

  it('continues to show the container after text deleted', () => {
    const parts = component();
    const counterEl = parts.counterEl;
    const textarea = parts.textarea;

    // Trigger the counter to be shown.
    textarea.value = 'Some text';
    textarea.dispatchEvent(new Event('input'));

    // Delete all the text in the textarea,
    textarea.value = '';
    textarea.dispatchEvent(new Event('input'));

    assert.equal(counterEl.innerHTML, '0/250');
  });

  it('reads the max length from the data-maxlength attribute', () => {
    const counterEl = component('foo', 500).counterEl;

    assert.equal(counterEl.innerHTML, '3/500');
  });

  it('updates the counter when text is added on "input" events', () => {
    const parts = component();
    const textarea = parts.textarea;
    const counterEl = parts.counterEl;

    textarea.value = 'testing';
    textarea.dispatchEvent(new Event('input'));

    assert.equal(counterEl.innerHTML, '7/250');
  });

  it('updates the counter when text is removed on "input" events', () => {
    const parts = component('Testing testing');
    const textarea = parts.textarea;
    const counterEl = parts.counterEl;

    // Make the text shorter.
    textarea.value = 'Testing';
    textarea.dispatchEvent(new Event('input'));

    assert.equal(counterEl.innerHTML, '7/250');
  });

  it('does not add error class when no pre-rendered text', () => {
    const counterEl = component(null, 5).counterEl;

    assert.equal(counterEl.classList.contains('is-too-long'),
                 false);
  });

  it('does not add error class when pre-rendered text short enough', () => {
    const counterEl = component('foo', 5).counterEl;

    assert.equal(counterEl.classList.contains('is-too-long'),
                 false);
  });

  it('adds an error class to the counter when pre-rendered value too long', () => {
    const counterEl = component('Too long', 5).counterEl;

    assert.equal(counterEl.classList.contains('is-too-long'),
                 true);
  });

  it('adds an error class to the counter when too much text entered', () => {
    const parts = component(null, 5);
    const counterEl = parts.counterEl;
    const textarea = parts.textarea;

    textarea.value = 'too long';
    textarea.dispatchEvent(new Event('input'));

    assert.equal(counterEl.classList.contains('is-too-long'),
                 true);
  });

  it('removes error class from counter when text reduced', () => {
    const parts = component('too long', 6);
    const counterEl = parts.counterEl;
    const textarea = parts.textarea;

    textarea.value = 'short';
    textarea.dispatchEvent(new Event('input'));

    assert.equal(counterEl.classList.contains('is-too-long'),
                 false);
  });
});
