'use strict';

var rangeUtil = require('../range-util');

describe('range-util', function () {
  var selection;
  var testNode;

  beforeEach(function () {
    selection = window.getSelection();
    selection.collapse();

    testNode = document.createElement('span');
    testNode.innerHTML = 'Some text content here';
    document.body.appendChild(testNode);
  });

  afterEach(function () {
    testNode.parentElement.removeChild(testNode);
  });

  function selectNode(node) {
    var range = testNode.ownerDocument.createRange();
    range.selectNodeContents(node);
    selection.addRange(range);
  }

  describe('#selectionEndPosition', function () {
    it('returns null if the selection is empty', function () {
      assert.isNull(rangeUtil.selectionEndPosition(selection));
    });

    it('returns a point if the selection is not empty', function () {
      selectNode(testNode);
      assert.ok(rangeUtil.selectionEndPosition(selection));
    });

    it('returns the top-left corner if the selection is backwards', function () {
      selectNode(testNode);
      selection.collapseToEnd();
      selection.extend(testNode, 0);
      var pos = rangeUtil.selectionEndPosition(selection);
      assert.equal(pos.left, testNode.offsetLeft);
    });

    it('returns the bottom-right corner if the selection is forwards', function () {
      selectNode(testNode);
      var pos = rangeUtil.selectionEndPosition(selection);
      assert.equal(pos.left, testNode.offsetLeft + testNode.offsetWidth);
    });
  });
});
