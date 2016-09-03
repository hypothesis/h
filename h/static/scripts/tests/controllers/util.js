'use strict';

/**
 * Helper to set up a component for a controller test
 *
 * @param {Document} document - Document to create component in
 * @param {string} template - HTML markup for the component
 * @param {Controller} controller - The controller class
 * @return {Controller} - The controller instance
 */
function setupComponent(document, template, ControllerClass) {
  var container = document.createElement('div');
  container.innerHTML = template;
  var root = container.firstChild;
  document.body.appendChild(root);
  container.remove();
  return new ControllerClass(root);
}

module.exports = {
  setupComponent: setupComponent,
};
