'use strict';

var upgradeElements = require('../../base/upgrade-elements');

describe('upgradeElements', function () {
  it('should upgrade elements matching selectors', function () {
    var TestController = sinon.spy();

    var root = document.createElement('div');
    root.classList.add('js-test');
    document.body.appendChild(root);

    upgradeElements(document.body, {'.js-test': TestController});
    assert.calledWith(TestController, root);

    root.remove();
  });

  it('does not upgrade elements if JS is disabled', function () {
    var TestController = sinon.spy();
    var root = {
      querySelectorAll: function () {
        // Array with one fake Element to upgrade
        return [{}];
      },
      ownerDocument: {
        location: { search: '?nojs=1' },
      },
    };
    upgradeElements(root, {'.js-test': TestController});
    assert.notCalled(TestController);
  });
});
