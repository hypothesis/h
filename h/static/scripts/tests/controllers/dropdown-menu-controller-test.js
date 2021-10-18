import { DropdownMenuController } from '../../controllers/dropdown-menu-controller';

import * as util from './util';

const TEMPLATE = [
  '<div class="js-dropdown-menu">',
  '<a href="#" data-ref="dropdownMenuToggle">Toggle</a>',
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

  function clickMenuLink() {
    toggleEl.dispatchEvent(new Event('click', { cancelable: true }));
  }

  it('should toggle menu on click', () => {
    clickMenuLink();
    assert.isTrue(isOpen());
    clickMenuLink();
    assert.isFalse(isOpen());
  });

  it('should toggle expanded state on click', () => {
    clickMenuLink();
    assert.equal(toggleEl.getAttribute('aria-expanded'), 'true');
    clickMenuLink();
    assert.equal(toggleEl.getAttribute('aria-expanded'), 'false');
  });

  it('should close menu on click outside', () => {
    clickMenuLink();
    document.body.dispatchEvent(new Event('click'));
    assert.isFalse(isOpen());
  });

  it('should not close menu on click inside', () => {
    clickMenuLink();
    menuEl.dispatchEvent(new Event('click'));
    assert.isTrue(isOpen());
  });
});
