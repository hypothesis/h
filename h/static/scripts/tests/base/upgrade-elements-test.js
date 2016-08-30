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
});
