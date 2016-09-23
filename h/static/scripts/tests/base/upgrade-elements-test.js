'use strict';

var Controller = require('../../base/controller');
var upgradeElements = require('../../base/upgrade-elements');

class TestController extends Controller {
  constructor(element, options) {
    super(element, options);
  }
}

describe('upgradeElements', function () {
  it('should upgrade elements matching selectors', function () {
    var root = document.createElement('div');
    root.innerHTML = '<div class="js-test"></div>';

    upgradeElements(root, {'.js-test': TestController});

    assert.instanceOf(root.children[0].controllers[0], TestController);
  });

  it('should unhide elements hidden until upgrade', function () {
    var root = document.createElement('div');
    root.innerHTML = '<div class="js-test is-hidden-when-loading"></div>';

    upgradeElements(root, {'.js-test': TestController});

    assert.equal(root.querySelectorAll('.is-hidden-when-loading').length, 0);
  });

  it('should unhide child elements hidden until upgrade', function () {
    var root = document.createElement('div');
    root.innerHTML = '<div class="js-test">' +
                     '<span class="is-hidden-when-loading"></span>' +
                     '</div>';

    upgradeElements(root, {'.js-test': TestController});

    assert.equal(root.querySelectorAll('.is-hidden-when-loading').length, 0);
  });

  describe('reload function', function () {
    var newContent = '<div class="js-test">Reloaded element</div>';

    function setupAndReload() {
      var root = document.createElement('div');
      root.innerHTML = '<div class="js-test">Original content</div>';
      upgradeElements(root, {'.js-test': TestController});

      var reloadFn = root.children[0].controllers[0].options.reload;
      var reloadResult = reloadFn(newContent);
      return {root: root, reloadResult: reloadResult};
    }

    it('replaces element markup', function () {
      var root = setupAndReload().root;
      assert.equal(root.innerHTML, newContent);
    });

    it('returns the replaced element', function () {
      var result = setupAndReload();
      assert.equal(result.root.children[0], result.reloadResult);
    });

    it('re-applies element upgrades', function () {
      var root = setupAndReload().root;
      var replacedElement = root.children[0];
      var ctrl = replacedElement.controllers[0];
      assert.instanceOf(ctrl, TestController);
    });
  });
});
