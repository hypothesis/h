'use strict';

var stringUtil = require('./string');

var hyphenate = stringUtil.hyphenate;

/**
 * Utility functions for DOM manipulation.
 */

/**
 * Replace a DOM element with an HTML string and return the new DOM element.
 *
 * @param {Element} el - DOM Element to replace
 * @param {string} html - HTML string that replaces the entire element
 */
function replaceElement(el, html) {
  if (!el.parentElement) {
    throw new Error('Cannot replace an element without a parent');
  }
  var parentEl = el.parentElement;
  var siblings = Array.from(parentEl.children);
  var nodeIndex = siblings.indexOf(el);
  el.outerHTML = html;
  return parentEl.children[nodeIndex];
}

/**
 * Set the state classes (`is-$state`) on an element.
 *
 * @param {Element} el
 * @param {Object} state - A map of state keys to boolean. For each key `k`,
 *                 the class `is-$k` will be added to the element if the value
 *                 is true or removed otherwise.
 */
function setElementState(el, state) {
  Object.keys(state).forEach(function (key) {
    var stateClass = 'is-' + hyphenate(key);
    el.classList.toggle(stateClass, !!state[key]);
  });
}

module.exports = {
  replaceElement: replaceElement,
  setElementState: setElementState,
};
