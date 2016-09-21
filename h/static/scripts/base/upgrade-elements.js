'use strict';

/**
 * Upgrade elements on the page with additional functionality
 *
 * Controllers attached to upgraded elements are accessible via the `controllers`
 * property on the element.
 *
 * @param {Element} root - The root element to search for matching elements
 * @param {Object} controllers - Object mapping selectors to controller classes.
 *        For each element matching a given selector, an instance of the
 *        controller class will be constructed and passed the element in
 *        order to upgrade it.
 */
function upgradeElements(root, controllers) {
  Object.keys(controllers).forEach(function (selector) {
    var elements = Array.from(root.querySelectorAll(selector));
    elements.forEach(function (el) {
      var ControllerClass = controllers[selector];
      try {
        new ControllerClass(el);
      } catch (err) {
        console.error('Failed to upgrade element %s with controller', el, ControllerClass, ':', err.toString());

        // Re-raise error so that Raven can capture and report it
        throw err;
      }
    });
  });
}

module.exports = upgradeElements;
