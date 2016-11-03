'use strict';

var DropdownMenuController = require('../../controllers/dropdown-menu-controller');
var util = require('./util');

var TEMPLATE = [
  '<div class="js-dropdown-menu">',
  '<span data-ref="dropdownMenuToggle">Toggle</span>',
  '<span data-ref="dropdownMenuContent">Menu</span>',
  '</div>',
].join('\n');

describe('DropdownMenuController', function () {
  var ctrl;
  var toggleEl;
  var menuEl;

  beforeEach(function () {
    ctrl = util.setupComponent(document, TEMPLATE, DropdownMenuController);
    toggleEl = ctrl.refs.dropdownMenuToggle;
    menuEl = ctrl.refs.dropdownMenuContent;
  });

  afterEach(function () {
    ctrl.element.remove();
  });

  function isOpen() {
    return menuEl.classList.contains('is-open');
  }

  it('should toggle menu on click', function () {
    toggleEl.dispatchEvent(new Event('click'));
    assert.isTrue(isOpen());
    toggleEl.dispatchEvent(new Event('click'));
    assert.isFalse(isOpen());
  });

  it('should close menu on click outside', function () {
    toggleEl.dispatchEvent(new Event('click'));
    document.body.dispatchEvent(new Event('click'));
    assert.isFalse(isOpen());
  });

  it('should not close menu on click inside', function () {
    toggleEl.dispatchEvent(new Event('click'));
    menuEl.dispatchEvent(new Event('click'));
    assert.isTrue(isOpen());
  });
});
