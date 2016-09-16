'use strict';

var Controller = require('../base/controller');
var setElementState = require('../util/dom').setElementState;

/**
 * Controller for the search bar.
 */
class SearchBarController extends Controller {
  constructor(element) {
    super(element);

    this._input = this.refs.searchBarInput;
    this._dropdown = this.refs.searchBarDropdown;
    this._dropdownItems = Array.from(
      element.querySelectorAll('[data-ref="searchBarDropdownItem"]'));

    var getActiveDropdownItem = () => {
      return element.querySelector('.js-search-bar-dropdown-menu-item--active');
    };

    var clearActiveDropdownItem = () => {
      var activeItem = getActiveDropdownItem();
      if (activeItem) {
        activeItem.classList.remove('js-search-bar-dropdown-menu-item--active');
      }
    };

    var updateActiveDropdownItem = element => {
      clearActiveDropdownItem();
      element.classList.add('js-search-bar-dropdown-menu-item--active');
    };

    var selectFacet = facet => {
      this._input.value = this._input.value + facet;

      closeDropdown();

      setTimeout(function() {
        this._input.focus();
      }.bind(this), 0);
    };

    var getPreviousSiblingElement = element => {
      if (!element) {
        return null;
      }

      do {
        element = element.previousSibling;
      } while (element && element.nodeType != 1);

      return element;
    };

    var getNextSiblingElement = element => {
      if (!element) {
        return null;
      }

      do {
        element = element.nextSibling;
      } while (element && element.nodeType != 1);

      return element;
    };

    var closeDropdown = () => {
      clearActiveDropdownItem();
      this.setState({open: false});
      this._input.removeEventListener('keydown', setupListenerKeys,
        true /*capture*/);
    };

    var openDropdown = () => {
      this.setState({open: true});
      this._input.addEventListener('keydown', setupListenerKeys,
        true /*capture*/);
    };

    var setupListenerKeys = event => {
      const ENTER_KEY_CODE = 13;
      const UP_ARROW_KEY_CODE = 38;
      const DOWN_ARROW_KEY_CODE = 40;

      var activeItem = getActiveDropdownItem();
      var handlers = {};

      var handleEnterKey = event => {
        event.preventDefault();

        if (activeItem) {
          var facet =
            activeItem.
              querySelector('[data-ref="searchBarDropdownItemTitle"]').
              innerHTML.trim();
          selectFacet(facet);
        }
      };

      var handleUpArrowKey = event => {
        updateActiveDropdownItem(getPreviousSiblingElement(activeItem) ||
          this._dropdownItems[this._dropdownItems.length - 1]);
      };

      var handleDownArrowKey = event => {
        updateActiveDropdownItem(getNextSiblingElement(activeItem) ||
          this._dropdownItems[0]);
      };

      handlers[ENTER_KEY_CODE] = handleEnterKey;
      handlers[UP_ARROW_KEY_CODE] = handleUpArrowKey;
      handlers[DOWN_ARROW_KEY_CODE] = handleDownArrowKey;

      var handler = handlers[event.keyCode];
      if (handler) {
        handler(event);
      }
    };

    var handleClickOnItem = event => {
      var facet =
        event.currentTarget.
          querySelector('[data-ref="searchBarDropdownItemTitle"]').
          innerHTML.trim();
      selectFacet(facet);
    };

    var handleHoverOnItem = event => {
      updateActiveDropdownItem(event.currentTarget);
    };

    var handleClickOnDropdown = event => {
      // prevent clicking on a part of the dropdown menu itself that
      // isn't one of the suggestions from closing the menu
      event.preventDefault();
    };

    var handleFocusOutside = event => {
      if (!element.contains(event.target) ||
        !element.contains(event.relatedTarget)) {
        this.setState({open: false});
      }
      closeDropdown();
    };

    var handleFocusOnInput = () => {
      if (this._input.value.trim().length > 0) {
        closeDropdown();
      } else {
        openDropdown();
      }
    };

    Object.keys(this._dropdownItems).forEach(function(key) {
      var item = this._dropdownItems[key];
      if(item && item.addEventListener) {
        item.addEventListener('mouseover', handleHoverOnItem,
          true);
        item.addEventListener('mousedown', handleClickOnItem,
          true);
      }
    }.bind(this));

    this._dropdown.addEventListener('mousedown', handleClickOnDropdown,
      true /*capture*/);
    this._input.addEventListener('focusout', handleFocusOutside,
      true /*capture*/);
    this._input.addEventListener('input', handleFocusOnInput,
      true /*capture*/);
    this._input.addEventListener('focusin', handleFocusOnInput,
      true /*capture*/);
  }

  update(state) {
    setElementState(this._dropdown, {open: state.open});
  }
}

module.exports = SearchBarController;
