'use strict';

function translate(rect, x, y) {
  return {
    left: rect.left + x,
    top: rect.top + y,
    width: rect.width,
    height: rect.height,
  };
}

function mapViewportRectToDocument(window, rect) {
  // `pageXOffset` and `pageYOffset` are used rather than `scrollX`
  // and `scrollY` for IE 10/11 compatibility.
  return translate(rect, window.pageXOffset, window.pageYOffset);
}

/**
 * Returns true if the start point of a selection occurs after the end point,
 * in document order.
 */
function isSelectionBackwards(selection) {
  if (selection.focusNode === selection.anchorNode) {
    return selection.focusOffset < selection.anchorOffset;
  }

  var range = selection.getRangeAt(0);
  return range.startContainer === selection.focusNode;
}

/**
 * Returns true if `node` is between the `startContainer` and `endContainer` of
 * the given `range`, inclusive.
 *
 * @param {Range} range
 * @param {Node} node
 */
function isNodeInRange(range, node) {
  if (node === range.startContainer || node === range.endContainer) {
    return true;
  }

  /* jshint -W016 */
  var isAfterStart = range.startContainer.compareDocumentPosition(node) &
   Node.DOCUMENT_POSITION_FOLLOWING;
  var isBeforeEnd = range.endContainer.compareDocumentPosition(node) &
   Node.DOCUMENT_POSITION_PRECEDING;

  return isAfterStart && isBeforeEnd;
}

/**
 * Iterate over all Node(s) in `range` in document order and invoke `callback`
 * for each of them.
 *
 * @param {Range} range
 * @param {Function} callback
 */
function forEachNodeInRange(range, callback) {
  var root = range.commonAncestorContainer;

  // The `whatToShow`, `filter` and `expandEntityReferences` arguments are
  // mandatory in IE although optional according to the spec.
  var nodeIter = root.ownerDocument.createNodeIterator(root,
    NodeFilter.SHOW_ALL, null /* filter */, false /* expandEntityReferences */);

  /* jshint -W084 */
  var currentNode;
  while (currentNode = nodeIter.nextNode()) {
    if (isNodeInRange(range, currentNode)) {
      callback(currentNode);
    }
  }
}

/**
 * Returns the bounding rectangles of non-whitespace text nodes in `range`.
 *
 * @param {Range} range
 * @return {Array<Rect>} Array of bounding rects in document coordinates.
 */
function getTextBoundingBoxes(range) {
  var whitespaceOnly = /^\s*$/;
  var textNodes = [];
  forEachNodeInRange(range, function (node) {
    if (node.nodeType === Node.TEXT_NODE &&
        !node.textContent.match(whitespaceOnly)) {
      textNodes.push(node);
    }
  });

  var rects = [];
  textNodes.forEach(function (node) {
    var nodeRange = node.ownerDocument.createRange();
    nodeRange.selectNodeContents(node);
    if (node === range.startContainer) {
      nodeRange.setStart(node, range.startOffset);
    }
    if (node === range.endContainer) {
      nodeRange.setEnd(node, range.endOffset);
    }
    if (nodeRange.collapsed) {
      // If the range ends at the start of this text node or starts at the end
      // of this node then do not include it.
      return;
    }

    // Measure the range and translate from viewport to document coordinates
    var viewportRects = Array.from(nodeRange.getClientRects());
    nodeRange.detach();
    rects = rects.concat(viewportRects.map(function (rect) {
      return mapViewportRectToDocument(node.ownerDocument.defaultView, rect);
    }));
  });
  return rects;
}

/**
 * Returns the rectangle for the line of text containing the focus point
 * of a Selection.
 *
 * @param {Selection} selection
 * @return {Object?} A rect containing the coordinates in the document of the
 *         line of text containing the focus point of the selection.
 */
function selectionFocusRect(selection) {
  if (selection.isCollapsed) {
    return null;
  }
  var textBoxes = getTextBoundingBoxes(selection.getRangeAt(0));
  if (textBoxes.length === 0) {
    return null;
  }

  if (isSelectionBackwards(selection)) {
    return textBoxes[0];
  } else {
    return textBoxes[textBoxes.length - 1];
  }
}

module.exports = {
  isSelectionBackwards: isSelectionBackwards,
  selectionFocusRect: selectionFocusRect,
};
