/**
 * Mark an element as having been upgraded.
 */
function markReady(element) {
  const HIDE_CLASS = 'is-hidden-when-loading';
  const hideOnLoad = Array.from(element.querySelectorAll('.' + HIDE_CLASS));
  hideOnLoad.forEach(el => {
    el.classList.remove(HIDE_CLASS);
  });
  element.classList.remove(HIDE_CLASS);
}

// List of all elements which have had upgrades applied
let upgradedElements = [];

/**
 * Remove all of the controllers for elements under `root`.
 *
 * This clears the `controllers` list for all elements under `root` and notifies
 * the controllers that their root element is about to be removed from the
 * document.
 */
function removeControllers(root) {
  upgradedElements = upgradedElements.filter(el => {
    if (root.contains(el)) {
      el.controllers.forEach(ctrl => ctrl.beforeRemove());
      el.controllers = [];
      return false;
    } else {
      return true;
    }
  });
}

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
export function upgradeElements(root, controllers) {
  // A helper which replaces the content (including the root element) of
  // an upgraded element with new markup and re-applies element upgrades to
  // the new root element
  function reload(element, html) {
    removeControllers(element);

    if (typeof html !== 'string') {
      throw new Error('Replacement markup must be a string');
    }
    const container = document.createElement('div');
    container.innerHTML = html;
    upgradeElements(container, controllers);

    const newElement = container.children[0];
    element.parentElement.replaceChild(newElement, element);
    return newElement;
  }

  Object.keys(controllers).forEach(selector => {
    const elements = Array.from(root.querySelectorAll(selector));
    elements.forEach(el => {
      const ControllerClass = controllers[selector];
      try {
        new ControllerClass(el, {
          reload: reload.bind(null, el),
        });
        upgradedElements.push(el);
        markReady(el);
      } catch (err) {
        console.error(
          'Failed to upgrade element %s with controller',
          el,
          ControllerClass,
          ':',
          err.toString()
        );

        // Re-raise error so that Raven can capture and report it
        throw err;
      }
    });
  });
}
