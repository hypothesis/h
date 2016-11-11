'use strict';

/**
 * Helper to set up a component for a controller test
 *
 * @param {Document} document - Document to create component in
 * @param {string} template - HTML markup for the component
 * @param {Controller} controller - The controller class
 * @param {Object} [options] - Options to pass to the controller constructor
 * @return {Controller} - The controller instance
 */
function setupComponent(document, template, ControllerClass, options) {
  const container = document.createElement('div');
  container.innerHTML = template;
  const root = container.firstChild;
  document.body.appendChild(root);
  container.remove();
  return new ControllerClass(root, options);
}

module.exports = {
  setupComponent: setupComponent,
};
