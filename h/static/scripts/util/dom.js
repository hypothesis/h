import * as stringUtil from './string';

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
export function setElementState(el, state) {
  Object.keys(state).forEach(key => {
    const stateClass = 'is-' + hyphenate(key);
    if (state[key]) {
      el.classList.add(stateClass);
    } else {
      el.classList.remove(stateClass);
    }
  });
}

/**
 * Search the DOM tree starting at `el` and return a map of "data-ref" attribute
 * values to elements.
 *
 * This provides a way to label parts of a control in markup and get a
 * reference to them subsequently in code.
 */
export function findRefs(el) {
  const map = {};

  const descendantsWithRef = el.querySelectorAll('[data-ref]');
  for (let i = 0; i < descendantsWithRef.length; i++) {
    // Use `Element#getAttribute` rather than `Element#dataset` to support IE 10
    // and avoid https://bugs.webkit.org/show_bug.cgi?id=161454
    const refEl = descendantsWithRef[i];
    const refs = (refEl.getAttribute('data-ref') || '').split(' ');
    refs.forEach(ref => {
      map[ref] = refEl;
    });
  }

  return map;
}

/**
 * Return the first child of `node` which is an `Element`.
 *
 * Work around certain browsers (IE, Edge) not supporting firstElementChild on
 * Document, DocumentFragment.
 *
 * @param {Node} node
 */
function firstElementChild(node) {
  for (let i = 0; i < node.childNodes.length; i++) {
    if (node.childNodes[i].nodeType === Node.ELEMENT_NODE) {
      return node.childNodes[i];
    }
  }
  // istanbul ignore next
  return null;
}

/**
 * Clone the content of a <template> element and return the first child Element.
 *
 * @param {HTMLTemplateElement} templateEl
 */
export function cloneTemplate(templateEl) {
  if (templateEl.content) {
    // <template> supported natively.
    const content = templateEl.content.cloneNode(true);
    return firstElementChild(content);
  } else {
    // <template> not supported. Browser just treats it as an unknown Element.
    return templateEl.firstElementChild.cloneNode(true);
  }
}
