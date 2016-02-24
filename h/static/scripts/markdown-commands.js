'use strict';

/**
 * Commands for toggling markdown formatting of a selection
 * in an input field.
 *
 * All of the functions in this module take as input the current state
 * of the input field, parameters for the operation to perform and return the
 * new state of the input field.
 */

/**
 * Describes the state of a plain text input field.
 *
 * interface EditorState {
 *   text: string;
 *   selectionStart: number;
 *   selectionEnd: number;
 * }
 */

/**
 * Types of Markdown link that can be inserted with
 * convertSelectionToLink()
 */
var LinkType = {
  ANCHOR_LINK: 0,
  IMAGE_LINK: 1,
};

/**
 * Replace text in an input field and return the new state.
 *
 * @param {EditorState} state - The state of the input field.
 * @param {number} pos - The start position of the text to remove.
 * @param {number} length - The number of characters to remove.
 * @param {string} text - The replacement text to insert at @p pos.
 * @return {EditorState} - The new state of the input field.
 */
function replaceText(state, pos, length, text) {
  var newSelectionStart = state.selectionStart;
  var newSelectionEnd = state.selectionEnd;

  if (newSelectionEnd <= pos) {
    // 1. Selection is before replaced text: Leave selection unchanged
  } else if (newSelectionStart >= pos + length) {
    // 2. Selection is after replaced text:
    //    Increment (start, end) by difference in length between original and
    //    replaced text
    newSelectionStart += text.length - length;
    newSelectionEnd += text.length - length;
  } else if (newSelectionStart <= pos &&
             newSelectionEnd >= pos + length) {
    // 3. Selection fully contains replaced text:
    //    Increment end by difference in length between original and replaced
    //    text
    newSelectionEnd += text.length - length;
  } else if (newSelectionStart < pos &&
             newSelectionEnd < pos + length) {
    // 4. Selection overlaps start but not end of replaced text:
    //    Decrement start to start of replacement text
    newSelectionStart = pos;
  } else if (newSelectionStart < pos + length &&
             newSelectionEnd > pos + length) {
    // 5. Selection overlaps end but not start of replaced text:
    //    Increment end by difference in length between original and replaced
    //    text
    newSelectionEnd += text.length - length;
  }

  return {
    text: state.text.slice(0, pos) + text + state.text.slice(pos + length),
    selectionStart: newSelectionStart,
    selectionEnd: newSelectionEnd,
  };
}

/**
 * Convert the selected text into a Markdown link.
 *
 * @param {EditorState} state - The current state of the input field.
 * @param {LinkType} linkType - The type of link to insert.
 * @return {EditorState} - The new state of the input field.
 */
function convertSelectionToLink(state, linkType) {
  if (typeof linkType === 'undefined') {
    linkType = LinkType.ANCHOR_LINK;
  }

  var selection = state.text.slice(state.selectionStart, state.selectionEnd);

  var linkPrefix = '';
  if (linkType === LinkType.IMAGE_LINK) {
    linkPrefix = '!';
  }

  var newState;
  if (selection.match(/[a-z]+:.*/)) {
    // Selection is a URL, wrap it with a link and use the selection as
    // the target.
    var dummyLabel = 'Description';
    newState = replaceText(state, state.selectionStart, selection.length,
      linkPrefix + '[' + dummyLabel + '](' + selection + ')');
    newState.selectionStart = state.selectionStart + linkPrefix.length + 1;
    newState.selectionEnd = newState.selectionStart + dummyLabel.length;
    return newState;
  } else {
    // Selection is not a URL, wrap it with a link and use the selection as
    // the label. Change the selection to the dummy link.
    var beforeURL = linkPrefix + '[' + selection + '](';
    var dummyLink = 'http://insert-your-link-here.com';
    newState = replaceText(state, state.selectionStart, selection.length,
      beforeURL + dummyLink + ')');
    newState.selectionStart = state.selectionStart + beforeURL.length;
    newState.selectionEnd = newState.selectionStart + dummyLink.length;
    return newState;
  }
}

/**
 * Toggle Markdown-style formatting around a span of text.
 *
 * @param {EditorState} state - The current state of the input field.
 * @param {string} prefix - The prefix to add or remove
 *                          before the selection.
 * @param {string?} suffix - The suffix to add or remove after the selection,
 *                           defaults to being the same as the prefix.
 * @param {string} placeholder - The text to insert between 'prefix' and
 *                               'suffix' if the input text is empty.
 * @return {EditorState} The new state of the input field.
 */
function toggleSpanStyle(state, prefix, suffix, placeholder) {
  if (typeof suffix === 'undefined') {
    suffix = prefix;
  }

  var selectionPrefix = state.text.slice(state.selectionStart - prefix.length,
    state.selectionStart);
  var selectionSuffix = state.text.slice(state.selectionEnd,
    state.selectionEnd + prefix.length);
  var newState = state;

  if (state.selectionStart === state.selectionEnd && placeholder) {
    newState = replaceText(state, state.selectionStart, 0, placeholder);
    newState.selectionEnd = newState.selectionStart + placeholder.length;
  }

  if (selectionPrefix === prefix && selectionSuffix === suffix) {
    newState = replaceText(newState, newState.selectionStart - prefix.length,
                           prefix.length, '');
    newState = replaceText(newState, newState.selectionEnd, suffix.length, '');
  } else {
    newState = replaceText(newState, newState.selectionStart, 0, prefix);
    newState = replaceText(newState, newState.selectionEnd, 0, suffix);
  }

  return newState;
}

/**
 * Toggle Markdown-style formatting around a block of text.
 *
 * @param {EditorState} state - The current state of the input field.
 * @param {string} prefix - The prefix to add or remove before each line
 *                          of the selection.
 * @return {EditorState} - The new state of the input field.
 */
function toggleBlockStyle(state, prefix) {
  // Expand the start and end of the selection to the start and
  // and of their respective lines
  var start = state.text.lastIndexOf('\n', state.selectionStart);
  if (start < 0) {
    start = 0;
  } else {
    start += 1;
  }
  var end = state.text.indexOf('\n', state.selectionEnd);
  if (end < 0) {
    end = state.text.length;
  }

  // Test whether all input lines are already formatted with this style
  var lines = state.text.slice(start, end).split('\n');
  var prefixedLines = lines.filter(function (line) {
    return line.slice(0, prefix.length) === prefix;
  });

  var newLines;
  if (prefixedLines.length === lines.length) {
    // All lines already start with the block prefix, remove the formatting.
    newLines = lines.map(function (line) {
      return line.slice(prefix.length);
    });
  } else {
    // Add the block style to any lines which do not already have it applied
    newLines = lines.map(function (line) {
      if (line.slice(0, prefix.length) === prefix) {
        return line;
      } else {
        return prefix + line;
      }
    });
  }
  return replaceText(state, start, end - start, newLines.join('\n'));
}

module.exports = {
  toggleSpanStyle: toggleSpanStyle,
  toggleBlockStyle: toggleBlockStyle,
  convertSelectionToLink: convertSelectionToLink,
  LinkType: LinkType,
};
