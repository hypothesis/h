'use strict';

var DropdownMenuController = require('../controllers/dropdown-menu-controller');
var util = require('./util');

var TEMPLATE = ['<div class="js-dropdown-menu">',
                '<span class="js-dropdown-menu-toggle">Toggle</span>',
                '<span class="js-dropdown-menu-content">Menu</span>',
                '</div>'].join('\n');

describe('DropdownMenuController', function () {
  var container;
  var toggleEl;
  var menuEl;

  beforeEach(function () {
    container = util.setupComponent(document, TEMPLATE, {
      '.js-dropdown-menu': DropdownMenuController,
    });
    toggleEl = container.querySelector('.js-dropdown-menu-toggle');
    menuEl = container.querySelector('.js-dropdown-menu-content');
  });

  afterEach(function () {
    container.remove();
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
