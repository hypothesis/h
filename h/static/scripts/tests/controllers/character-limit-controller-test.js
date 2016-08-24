'use strict';

var CharacterLimitController = require('../../controllers/character-limit-controller');
var util = require('./util');

describe('CharacterLimitController', function () {

  var ctrl;

  afterEach(function () {
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

    var template = '<div class="js-character-limit">';
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

  it('adds the ready class', function () {
    var counterEl = component().counterEl;

    assert.equal(counterEl.classList.contains('is-ready'), true);
  });

  it('shows the counter initially even if textarea empty', function () {
    var counterEl = component().counterEl;

    assert.equal(counterEl.innerHTML, '0/250');
  });

  it('shows the counter if the element has pre-rendered text', function () {
    var counterEl = component('pre-rendered').counterEl;

    assert.equal(counterEl.innerHTML, '12/250');
  });

  it('continues to show the container after text deleted', function() {
    var parts = component();
    var counterEl = parts.counterEl;
    var textarea = parts.textarea;

    // Trigger the counter to be shown.
    textarea.value = 'Some text';
    textarea.dispatchEvent(new Event('input'));

    // Delete all the text in the textarea,
    textarea.value = '';
    textarea.dispatchEvent(new Event('input'));

    assert.equal(counterEl.innerHTML, '0/250');
  });

  it('reads the max length from the data-maxlength attribute', function () {
    var counterEl = component('foo', 500).counterEl;

    assert.equal(counterEl.innerHTML, '3/500');
  });

  it('updates the counter when text is added on "input" events', function () {
    var parts = component();
    var textarea = parts.textarea;
    var counterEl = parts.counterEl;

    textarea.value = 'testing';
    textarea.dispatchEvent(new Event('input'));

    assert.equal(counterEl.innerHTML, '7/250');
  });

  it('updates the counter when text is removed on "input" events', function () {
    var parts = component('Testing testing');
    var textarea = parts.textarea;
    var counterEl = parts.counterEl;

    // Make the text shorter.
    textarea.value = 'Testing';
    textarea.dispatchEvent(new Event('input'));

    assert.equal(counterEl.innerHTML, '7/250');
  });

  it('does not add error class when no pre-rendered text', function() {
    var counterEl = component(null, 5).counterEl;

    assert.equal(counterEl.classList.contains('is-too-long'),
                 false);
  });

  it('does not add error class when pre-rendered text short enough', function() {
    var counterEl = component('foo', 5).counterEl;

    assert.equal(counterEl.classList.contains('is-too-long'),
                 false);
  });

  it('adds an error class to the counter when pre-rendered value too long', function() {
    var counterEl = component('Too long', 5).counterEl;

    assert.equal(counterEl.classList.contains('is-too-long'),
                 true);
  });

  it('adds an error class to the counter when too much text entered', function() {
    var parts = component(null, 5);
    var counterEl = parts.counterEl;
    var textarea = parts.textarea;

    textarea.value = 'too long';
    textarea.dispatchEvent(new Event('input'));

    assert.equal(counterEl.classList.contains('is-too-long'),
                 true);
  });

  it('removes error class from counter when text reduced', function() {
    var parts = component('too long', 6);
    var counterEl = parts.counterEl;
    var textarea = parts.textarea;

    textarea.value = 'short';
    textarea.dispatchEvent(new Event('input'));

    assert.equal(counterEl.classList.contains('is-too-long'),
                 false);
  });
});
