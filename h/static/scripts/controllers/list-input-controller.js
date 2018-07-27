'use strict';

const Controller = require('../base/controller');
const { cloneTemplate } = require('../util/dom');

/**
 * Controller for list inputs.
 *
 * The default deform widget for editing sequences,
 * `deform.widget.SequenceWidget` has support for various options such as a
 * minimum and maximum number of items and drag-and-drop re-ordering, which are
 * not yet implemented here.
 */
class ListInputController extends Controller {
  constructor(element) {
    super(element);

    // Handle 'Add {item type}' button.
    this.refs.addItemButton.addEventListener('click', () => {
      const newItemEl = cloneTemplate(this.refs.itemTemplate);
      this.refs.itemList.appendChild(newItemEl);
    });

    // Handle 'Remove' button.
    element.addEventListener('click', (event) => {
      const btn = event.target.closest('button');
      if (btn.getAttribute('data-ref') === 'removeItemButton') {
        const parentItem = event.target.closest('li');
        parentItem.remove();
      }
    });
  }
}

module.exports = ListInputController;
