'use strict';

const ListInputController = require('../../controllers/list-input-controller');
const { setupComponent } = require('./util');

describe('ListInputController', () => {
  const template = `
  <div class="js-list-input">
    <template data-ref="itemTemplate">
      <li>
        <input name="an-input-field">
        <button data-ref="removeItemButton">Remove</button>
      </li>
    </template>

    <ul data-ref="itemList">
    </ul>

    <button data-ref="addItemButton">Add item</button>
  </div>
  `.trim();

  function itemCount(ctrl) {
    return ctrl.refs.itemList.querySelectorAll('li').length;
  }

  it('adds a new blank item when clicking "Add item" button', () => {
    const ctrl = setupComponent(document, template, ListInputController);
    ctrl.refs.addItemButton.click();
    assert.equal(itemCount(ctrl), 1);

    ctrl.refs.addItemButton.click();
    assert.equal(itemCount(ctrl), 2);
  });

  it('removes the item when clicking "Remove item" button', () => {
    const ctrl = setupComponent(document, template, ListInputController);
    ctrl.refs.addItemButton.click();

    const removeBtn = ctrl.element.querySelector('li > button');
    removeBtn.click();

    assert.equal(itemCount(ctrl), 1);
  });
});
