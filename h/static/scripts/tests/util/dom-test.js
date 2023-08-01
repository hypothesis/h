import * as domUtil from '../../util/dom';

describe('util/dom', () => {
  function createDOM(html) {
    const el = document.createElement('div');
    el.innerHTML = html;
    const child = el.children[0];
    document.body.appendChild(child);
    el.remove();
    return child;
  }

  describe('findRefs', () => {
    it('returns a map of name to DOM element', () => {
      const root = createDOM(`
        <div>
          <label data-ref="label">Input label</label>
          <input data-ref="input">
        </div>
      `);
      const labelEl = root.querySelector('label');
      const inputEl = root.querySelector('input');

      assert.deepEqual(domUtil.findRefs(root), {
        label: labelEl,
        input: inputEl,
      });
    });

    it('allows elements to have more than one name', () => {
      const root = createDOM('<div><div data-ref="one two"></div></div>');
      assert.deepEqual(domUtil.findRefs(root), {
        one: root.firstChild,
        two: root.firstChild,
      });
    });
  });

  describe('setElementState', () => {
    it('adds "is-$state" classes for keys with truthy values', () => {
      const btn = createDOM('<button></button>');
      domUtil.setElementState(btn, {
        visible: true,
      });
      assert.deepEqual(Array.from(btn.classList), ['is-visible']);
    });

    it('removes "is-$state" classes for keys with falsey values', () => {
      const btn = createDOM('<button class="is-hidden"></button>');
      domUtil.setElementState(btn, {
        hidden: false,
      });
      assert.deepEqual(Array.from(btn.classList), []);
    });
  });

  describe('cloneTemplate', () => {
    it('clones the first child of the template when <template> is supported', () => {
      const template = document.createElement('template');
      template.innerHTML = '<div id="child"></div>';
      const clone = domUtil.cloneTemplate(template);
      assert.deepEqual(clone.outerHTML, '<div id="child"></div>');
    });

    it('clones the first child of the template when <template> is not supported', () => {
      const template = createDOM(
        '<fake-template><div id="child"></div></fake-template>',
      );
      const clone = domUtil.cloneTemplate(template);
      assert.deepEqual(clone.outerHTML, '<div id="child"></div>');
    });
  });
});
