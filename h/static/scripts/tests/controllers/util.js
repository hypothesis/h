'use strict';

var upgradeElements = require('../../controllers/upgrade-elements');

/**
 * Helper to set up a component for a controller test
 *
 * @param {Document} document - Document to create component in
 * @param {string} template - HTML markup for the component
 * @param {object} controllers - Map of class names to controller classes used to
                   upgrade the components using `upgradeElements()`
 */
function setupComponent(document, template, controllers) {
  var container = document.createElement('div');
  container.innerHTML = template;
  document.body.appendChild(container);
  upgradeElements(container, controllers);
  return container;
}

module.exports = {
  setupComponent: setupComponent,
};

