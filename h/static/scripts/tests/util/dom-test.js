'use strict';

var domUtil = require('../../util/dom');

describe('util/dom', function () {
  function createDOM(html) {
    var el = document.createElement('div');
    el.innerHTML = html;
    var child = el.children[0];
    document.body.appendChild(child);
    el.remove();
    return child;
  }

  describe('findRefs', function () {
    it('returns a map of name to DOM element', function () {
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

    it('allows elements to have more than one name', function () {
      var root = createDOM('<div><div data-ref="one two"></div></div>');
      assert.deepEqual(domUtil.findRefs(root), {
        one: root.firstChild,
        two: root.firstChild,
      });
    });
  });

  describe('setElementState', function () {
    it('adds "is-$state" classes for keys with truthy values', function () {
      var btn = createDOM('<button></button>');
      domUtil.setElementState(btn, {
        visible: true,
      });
      assert.deepEqual(Array.from(btn.classList), ['is-visible']);
    });

    it('removes "is-$state" classes for keys with falsey values', function () {
      var btn = createDOM('<button class="is-hidden"></button>');
      domUtil.setElementState(btn, {
        hidden: false,
      });
      assert.deepEqual(Array.from(btn.classList), []);
    });
  });
});
