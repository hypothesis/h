'use strict';

var domUtil = require('../../util/dom');

describe('util/dom', () => {
  function createDOM(html) {
    var el = document.createElement('div');
    el.innerHTML = html;
    var child = el.children[0];
    document.body.appendChild(child);
    el.remove();
    return child;
  }

  describe('findRefs', () => {
    it('returns a map of name to DOM element', () => {
      var root = createDOM(`
        <div>
          <label data-ref="label">Input label</label>
          <input data-ref="input">
        </div>
      `);
      var labelEl = root.querySelector('label');
      var inputEl = root.querySelector('input');

      assert.deepEqual(domUtil.findRefs(root), {
        label: labelEl,
        input: inputEl,
      });
    });

    it('allows elements to have more than one name', () => {
      var root = createDOM('<div><div data-ref="one two"></div></div>');
      assert.deepEqual(domUtil.findRefs(root), {
        one: root.firstChild,
        two: root.firstChild,
      });
    });
  });

  describe('setElementState', () => {
    it('adds "is-$state" classes for keys with truthy values', () => {
      var btn = createDOM('<button></button>');
      domUtil.setElementState(btn, {
        visible: true,
      });
      assert.deepEqual(Array.from(btn.classList), ['is-visible']);
    });

    it('removes "is-$state" classes for keys with falsey values', () => {
      var btn = createDOM('<button class="is-hidden"></button>');
      domUtil.setElementState(btn, {
        hidden: false,
      });
      assert.deepEqual(Array.from(btn.classList), []);
    });
  });
});
