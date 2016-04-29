'use strict';

var rangeUtil = require('../range-util');

describe('range-util', function () {
  var selection;
  var testNode;

  beforeEach(function () {
    selection = window.getSelection();
    selection.collapse();

    testNode = document.createElement('span');
    testNode.innerHTML = 'Some text <br>content here';
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

  describe('#selectionFocusRect', function () {
    it('returns null if the selection is empty', function () {
      assert.isNull(rangeUtil.selectionFocusRect(selection));
    });

    it('returns a point if the selection is not empty', function () {
      selectNode(testNode);
      assert.ok(rangeUtil.selectionFocusRect(selection));
    });

    it('returns the first line\'s rect if the selection is backwards', function () {
      selectNode(testNode);
      selection.collapseToEnd();
      selection.extend(testNode, 0);
      var rect = rangeUtil.selectionFocusRect(selection);
      assert.equal(rect.left, testNode.offsetLeft);
      assert.equal(rect.top, testNode.offsetTop);
    });

    it('returns the last line\'s rect if the selection is forwards', function () {
      selectNode(testNode);
      var rect = rangeUtil.selectionFocusRect(selection);
      assert.equal(rect.left, testNode.offsetLeft);
      assert.equal(rect.top + rect.height, testNode.offsetTop + testNode.offsetHeight);
    });
  });
});
