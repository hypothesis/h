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
      this._input.value = facet;

      closeDropdown();

      setTimeout(function() {
        this._input.focus();
      }.bind(this), 0);
    };

    var isHidden = element => {
      return element &&
        (element.nodeType !== 1 ||
          !element.classList ||
          element.classList.contains('is-hidden'));
    };

    var getPreviousVisibleSiblingElement = element => {
      if (!element) {
        return null;
      }

      do {
        element = element.previousSibling;
      } while (isHidden(element));
      return element;
    };

    var getNextVisibleSiblingElement = element => {
      if (!element) {
        return null;
      }

      do {
        element = element.nextSibling;
      } while (isHidden(element));

      return element;
    };

    var showAllDropdownItems = () => {
      this._dropdownItems.forEach(function(dropdownItem) {
        dropdownItem.classList.remove('is-hidden');
      });
    };

    var closeDropdown = () => {
      if (!this.state.open) { return; }
      clearActiveDropdownItem();
      showAllDropdownItems();
      this.setState({open: false});
      this._input.removeEventListener('keydown', setupListenerKeys);
    };

    var openDropdown = () => {
      if (this.state.open) { return; }
      clearActiveDropdownItem();

      this.setState({open: true});

      this._input.addEventListener('keydown', setupListenerKeys);
    };

    var getVisibleDropdownItems = () => {
      return this._dropdown.querySelectorAll('li:not(.is-hidden)');
    };

    /** Show items that match the word and hide ones that don't. */
    var setVisibleDropdownItems = word => {
      this._dropdownItems.forEach(function(dropdownItem) {
        var dropdownItemTitle =
          dropdownItem.querySelector('[data-ref="searchBarDropdownItemTitle"]').
            innerHTML.trim();
        if (dropdownItemTitle.indexOf(word) < 0) {
          dropdownItem.classList.add('is-hidden');
        } else {
          dropdownItem.classList.remove('is-hidden');
        }
      });
    };

    var getTrimmedInputValue = () => {
      return this._input.value.trim();
    };

    var maybeOpenOrCloseDropdown = () => {
      var word = getTrimmedInputValue();
      var shouldOpenDropdown = true;

      // If there are no visible items that match the word close the dropdown
      if (getVisibleDropdownItems().length < 1) {
        shouldOpenDropdown = false;
      }

      // If the word has a ':' don't show dropdown
      if (word.indexOf(':') > -1) {
        shouldOpenDropdown = false;
      }

      if (shouldOpenDropdown) {
        openDropdown();
      } else {
        closeDropdown();
      }
    };

    var setupListenerKeys = event => {
      const ENTER_KEY_CODE = 13;
      const UP_ARROW_KEY_CODE = 38;
      const DOWN_ARROW_KEY_CODE = 40;

      var activeItem = getActiveDropdownItem();
      var handlers = {};

      var visibleDropdownItems = getVisibleDropdownItems();

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

      var handleUpArrowKey = () => {
        updateActiveDropdownItem(getPreviousVisibleSiblingElement(activeItem) ||
          visibleDropdownItems[visibleDropdownItems.length - 1]);
      };

      var handleDownArrowKey = () => {
        updateActiveDropdownItem(getNextVisibleSiblingElement(activeItem) ||
          visibleDropdownItems[0]);
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

    var handleFocusinOnInput = () => {
      maybeOpenOrCloseDropdown();
    };

    var handleInputOnInput = () => {
      var word = getTrimmedInputValue();
      setVisibleDropdownItems(word);
      maybeOpenOrCloseDropdown();
    };

    this._dropdownItems.forEach(function(item) {
      if(item && item.addEventListener) {
        item.addEventListener('mouseover', handleHoverOnItem);
        item.addEventListener('mousedown', handleClickOnItem);
      }
    });

    this._dropdown.addEventListener('mousedown', handleClickOnDropdown);
    this._input.addEventListener('blur', handleFocusOutside);
    this._input.addEventListener('input', handleInputOnInput);
    this._input.addEventListener('focus', handleFocusinOnInput);
  }

  update(state) {
    setElementState(this._dropdown, {open: state.open});
  }
}

module.exports = SearchBarController;
