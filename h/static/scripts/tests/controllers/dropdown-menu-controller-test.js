'use strict';

const DropdownMenuController = require('../../controllers/dropdown-menu-controller');
const util = require('./util');

const TEMPLATE = [
  '<div class="js-dropdown-menu">',
  '<span data-ref="dropdownMenuToggle">Toggle</span>',
  '<span data-ref="dropdownMenuContent">Menu</span>',
  '</div>',
].join('\n');

describe('DropdownMenuController', () => {
  let ctrl;
  let toggleEl;
  let menuEl;

  beforeEach(() => {
    ctrl = util.setupComponent(document, TEMPLATE, DropdownMenuController);
    toggleEl = ctrl.refs.dropdownMenuToggle;
    menuEl = ctrl.refs.dropdownMenuContent;
  });

  afterEach(() => {
    ctrl.element.remove();
  });

  function isOpen() {
    return menuEl.classList.contains('is-open');
  }

  it('should toggle menu on click', () => {
    toggleEl.dispatchEvent(new Event('click'));
    assert.isTrue(isOpen());
    toggleEl.dispatchEvent(new Event('click'));
    assert.isFalse(isOpen());
  });

  it('should close menu on click outside', () => {
    toggleEl.dispatchEvent(new Event('click'));
    document.body.dispatchEvent(new Event('click'));
    assert.isFalse(isOpen());
  });

  it('should not close menu on click inside', () => {
    toggleEl.dispatchEvent(new Event('click'));
    menuEl.dispatchEvent(new Event('click'));
    assert.isTrue(isOpen());
  });
});
