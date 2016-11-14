'use strict';

const Controller = require('../../base/controller');
const upgradeElements = require('../../base/upgrade-elements');

class TestController extends Controller {
  constructor(element, options) {
    super(element, options);
  }
}

describe('upgradeElements', () => {
  it('should upgrade elements matching selectors', () => {
    const root = document.createElement('div');
    root.innerHTML = '<div class="js-test"></div>';

    upgradeElements(root, {'.js-test': TestController});

    assert.instanceOf(root.children[0].controllers[0], TestController);
  });

  it('should unhide elements hidden until upgrade', () => {
    const root = document.createElement('div');
    root.innerHTML = '<div class="js-test is-hidden-when-loading"></div>';

    upgradeElements(root, {'.js-test': TestController});

    assert.equal(root.querySelectorAll('.is-hidden-when-loading').length, 0);
  });

  it('should unhide child elements hidden until upgrade', () => {
    const root = document.createElement('div');
    root.innerHTML = '<div class="js-test">' +
                     '<span class="is-hidden-when-loading"></span>' +
                     '</div>';

    upgradeElements(root, {'.js-test': TestController});

    assert.equal(root.querySelectorAll('.is-hidden-when-loading').length, 0);
  });

  describe('reload function', () => {
    const newContent = '<div class="js-test">Reloaded element</div>';

    function setupAndReload() {
      const root = document.createElement('div');
      root.innerHTML = '<div class="js-test">Original content</div>';
      upgradeElements(root, {'.js-test': TestController});

      const reloadFn = root.children[0].controllers[0].options.reload;
      const reloadResult = reloadFn(newContent);
      return {root: root, reloadResult: reloadResult};
    }

    it('replaces element markup', () => {
      const root = setupAndReload().root;
      assert.equal(root.innerHTML, newContent);
    });

    it('returns the replaced element', () => {
      const result = setupAndReload();
      assert.equal(result.root.children[0], result.reloadResult);
    });

    it('re-applies element upgrades', () => {
      const root = setupAndReload().root;
      const replacedElement = root.children[0];
      const ctrl = replacedElement.controllers[0];
      assert.instanceOf(ctrl, TestController);
    });

    it('calls #beforeRemove on the original controllers', () => {
      const root = document.createElement('div');
      root.innerHTML = '<div class="js-test">Original content</div>';
      upgradeElements(root, {'.js-test': TestController});
      const ctrl = root.children[0].controllers[0];
      ctrl.beforeRemove = sinon.stub();
      const reloadFn = ctrl.options.reload;

      reloadFn(newContent);

      assert.called(ctrl.beforeRemove);
    });
  });
});
