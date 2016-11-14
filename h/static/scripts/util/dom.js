'use strict';

const stringUtil = require('./string');

const hyphenate = stringUtil.hyphenate;

/**
 * Utility functions for DOM manipulation.
 */

/**
 * Set the state classes (`is-$state`) on an element.
 *
 * @param {Element} el
 * @param {Object} state - A map of state keys to boolean. For each key `k`,
 *                 the class `is-$k` will be added to the element if the value
 *                 is true or removed otherwise.
 */
function setElementState(el, state) {
  Object.keys(state).forEach((key) => {
    const stateClass = 'is-' + hyphenate(key);
    el.classList.toggle(stateClass, !!state[key]);
  });
}

/**
 * Search the DOM tree starting at `el` and return a map of "data-ref" attribute
 * values to elements.
 *
 * This provides a way to label parts of a control in markup and get a
 * reference to them subsequently in code.
 */
function findRefs(el) {
  const map = {};

  const descendantsWithRef = el.querySelectorAll('[data-ref]');
  for (let i=0; i < descendantsWithRef.length; i++) {
    // Use `Element#getAttribute` rather than `Element#dataset` to support IE 10
    // and avoid https://bugs.webkit.org/show_bug.cgi?id=161454
    const refEl = descendantsWithRef[i];
    const refs = (refEl.getAttribute('data-ref') || '').split(' ');
    refs.forEach((ref) => {
      map[ref] = refEl;
    });
  }

  return map;
}

module.exports = {
  findRefs: findRefs,
  setElementState: setElementState,
};
