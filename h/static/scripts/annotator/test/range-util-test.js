'use strict';

var rangeUtil = require('../range-util');

function createRange(node, start, end) {
  var range = node.ownerDocument.createRange();
  range.setStart(node, start);
  range.setEnd(node, end);
  return range;
}

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

  describe('#isNodeInRange', function () {
    it('is true for a node in the range', function () {
      var rng = createRange(testNode, 0, 1);
      assert.equal(rangeUtil.isNodeInRange(rng, testNode.firstChild), true);
    });

    it('is false for a node before the range', function () {
      testNode.innerHTML = 'one <b>two</b> three';
      var rng = createRange(testNode, 1, 2);
      assert.equal(rangeUtil.isNodeInRange(rng, testNode.firstChild), false);
    });

    it('is false for a node after the range', function () {
      testNode.innerHTML = 'one <b>two</b> three';
      var rng = createRange(testNode, 1, 2);
      assert.equal(rangeUtil.isNodeInRange(rng, testNode.childNodes.item(2)), false);
    });
  });

  describe('#getTextBoundingBoxes', function () {
    it('gets the bounding box of a range in a text node', function () {
      testNode.innerHTML = 'plain text';
      var rng = createRange(testNode.firstChild, 0, 5);
      var boxes = rangeUtil.getTextBoundingBoxes(rng);
      assert.ok(boxes.length);
    });

    it('gets the bounding box of a range containing a text node', function () {
      testNode.innerHTML = 'plain text';
      var rng = createRange(testNode, 0, 1);
      var boxes = rangeUtil.getTextBoundingBoxes(rng);
      assert.ok(boxes.length);
    });
  });

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
