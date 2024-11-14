import { Controller } from '../base/controller';

import { setElementState } from '../util/dom';

import updateHelper from '../util/update-helpers.js';

const ENTER = 13;
const UP = 38;
const DOWN = 40;

/**
 * Controller for adding autosuggest control to a piece of the page
 */
export class AutosuggestDropdownController extends Controller {
  /*
   * @typedef {Object} ConfigOptions
   * @property {Function} renderListItem - called with every item in the list
   *   after the listFilter function is called. The return value will be the final
   *   html that is set in the list item DOM.
   * @property {Function} listFilter - called at initialization, focus of input,
   *   and input changes made by user. The function will receieve the full list
   *   and the current value of the input. This is meant to be an pure function
   *   that will return a filtered list based on the consumer's domain needs.
   * @property {Function} onSelect - called once the user has made a selection of an
   *   item in the autosuggest. It will receive the item selected as the only argument.
   * @property {Object} [classNames] - this is the enumerated list of class name
   *   overrides for consumers to customize the UI.
   *   Possible values: { container, list, item, activeItem, header }
   * @property {String} [header] - value of the header label at top of suggestions
   */

  /**
   * @param {HTMLInputElement} inputElement that we are responding to in order to provide
   *    suggestions. Note, we will add the suggestion container as a sibling to this
   *    element.
   * @param {ConfigOptions} configOptions are used to set the initial set of items and the header
   *    as well as providing the hooks for updates and callbacks
   *
   */
  constructor(inputElement, configOptions) {
    super(inputElement, configOptions);

    if (!configOptions.renderListItem) {
      // istanbul ignore next
      throw new Error(
        'Missing renderListItem callback in AutosuggestDropdownController constructor',
      );
    }

    if (!configOptions.listFilter) {
      // istanbul ignore next
      throw new Error(
        'Missing listFilter function in AutosuggestDropdownController constructor',
      );
    }

    if (!configOptions.onSelect) {
      // istanbul ignore next
      throw new Error(
        'Missing onSelect callback in AutosuggestDropdownController constructor',
      );
    }

    // set up our element class attribute enum values
    // Note, we currently are not doing anything with the default
    // classes, but we have them if we wanted to give something for a default
    // styling.
    if (configOptions.classNames) {
      this.options.classNames.container =
        configOptions.classNames.container || 'autosuggest__container';
      this.options.classNames.list =
        configOptions.classNames.list || 'autosuggest__list';
      this.options.classNames.item =
        configOptions.classNames.item || 'autosuggest__list-item';
      this.options.classNames.activeItem =
        configOptions.classNames.activeItem || 'autosuggest__list-item--active';
      this.options.classNames.header =
        configOptions.classNames.header || 'autosuggest__header';
    }

    // renaming simply to make it more obvious what
    // the element is in other contexts of the controller
    this._input = this.element;

    // initial state values
    this.setState({
      visible: false,
      header: configOptions.header || '',

      // working list that are displayed to use
      list: [],

      // rootList is the original set that the filter
      // will receive to determine what should be shown
      rootList: [],
    });

    this._setList(configOptions.list);

    // Public API
    this.setHeader = this._setHeader;
  }

  update(newState, prevState) {
    // if our prev state is empty then
    // we assume that this is the first update/render call
    if (!('visible' in prevState)) {
      // create the elements that make up the component
      this._renderContentContainers();
      this._addTopLevelEventListeners();
    }

    if (newState.visible !== prevState.visible) {
      // updates the dom to change the class which actually updates visibilty
      setElementState(this._suggestionContainer, { open: newState.visible });
    }

    if (newState.header !== prevState.header) {
      this._header.innerHTML = newState.header;
    }

    const listChanged = updateHelper.listIsDifferent(
      newState.list,
      prevState.list,
    );

    if (listChanged) {
      this._renderListItems();
    }

    // list change detection is needed to persist the
    // currently active elements over to the new list
    if (newState.activeId !== prevState.activeId || listChanged) {
      const currentActive = this._getActiveListItemElement();

      if (prevState.activeId && currentActive) {
        currentActive.classList.remove(this.options.classNames.activeItem);
      }

      if (
        newState.activeId &&
        newState.list.find(item => item.__suggestionId === newState.activeId)
      ) {
        this._listContainer
          .querySelector(`[data-suggestion-id="${newState.activeId}"]`)
          .classList.add(this.options.classNames.activeItem);
      }
    }
  }

  /**
   * sets what would be the top header html
   *  to give context of what the suggestions are for
   *
   * @param  {string} header Html to place in header. You can pass plain text
   *  as well.
   */
  _setHeader(header) {
    this.setState({
      header,
    });
  }

  /**
   * update the current list
   *
   * @param  {Array} list The new list.
   */
  _setList(list) {
    if (!Array.isArray(list)) {
      // istanbul ignore next
      throw new TypeError('setList requires an array first argument');
    }

    this.setState({
      rootList: list.map(item => {
        return Object.assign({}, item, {
          // create an id that lets us direction map
          // selection to arbitrary item in list.
          // This allows lists to pass more than just the required
          // `name` property to know more about what the list item is
          __suggestionId: Math.random().toString(36).substr(2, 5),
        });
      }),
    });

    this._filterListFromInput();
  }

  /**
   * we will run the consumer's filter function
   *  that is expected to be a pure function that will receive the
   *  root list (the initial list or list made with setList) and
   *  the input's current value. that function will return the array items,
   *  filtered and sorted, that will be set the new working list state and
   *  be rerendered.
   */
  _filterListFromInput() {
    this.setState({
      list:
        this.options.listFilter(this.state.rootList, this._input.value) || [],
    });
  }

  /**
   * hit the consumers filter function to determine
   *   if we still have list items that need to be shown to the user.
   */
  _filterAndToggleVisibility() {
    this._filterListFromInput();

    this._toggleSuggestionsVisibility(/*show*/ this.state.list.length > 0);
  }

  /**
   * lookup the active element, get item from
   *  object from list that was passed in, and invoke the onSelect callback.
   *  This is process to actually make a selection
   */
  _selectCurrentActiveItem() {
    const currentActive = this._getActiveListItemElement();
    const suggestionId =
      currentActive && currentActive.getAttribute('data-suggestion-id');
    const selection = this.state.list.filter(item => {
      return item.__suggestionId === suggestionId;
    })[0];

    if (selection) {
      this.options.onSelect(selection);
      this._filterAndToggleVisibility();
      this.setState({
        activeId: null,
      });
    }
  }

  /**
   * update the list item dom elements with
   *  their "active" state when the user is hovering.
   *
   * @param  {bool} hovering are we hovering on the current element
   * @param  {Event} event    event used to pull the list item being targeted
   */
  _toggleItemHoverState(hovering, event) {
    const currentActive = this._getActiveListItemElement();
    const target = event.currentTarget;

    if (hovering && currentActive && currentActive.contains(target)) {
      // istanbul ignore next
      return;
    }

    this.setState({
      activeId: hovering ? target.getAttribute('data-suggestion-id') : null,
    });
  }

  /**
   * this function piggy backs on the setElementState
   *  style of defining element state in its class. Used in combination with the
   *  this.options.classNames.container the consumer has easy access to what the visibility state
   *  of the container is.
   *
   * @param  {bool} show should we update the state to be visible or not
   */
  _toggleSuggestionsVisibility(show) {
    // keeps the internal state synced with visibility
    this.setState({
      visible: !!show,
    });
  }

  /**
   * @returns {HTMLElement}  the active list item element
   */
  _getActiveListItemElement() {
    return this._listContainer.querySelector(
      '.' + this.options.classNames.activeItem,
    );
  }

  /**
   * navigate the list, toggling the active item,
   *  based on the users arrow directions
   *
   * @param  {bool} down is the user navigating down the list?
   */
  _keyboardSelectionChange(down) {
    const currentActive = this._getActiveListItemElement();
    let nextActive;

    // we have a starting point, navigate on siblings of current
    if (currentActive) {
      if (down) {
        nextActive = currentActive.nextSibling;
      } else {
        nextActive = currentActive.previousSibling;
      }

      // we have no starting point, let's navigate based on
      // the directional expectation of what the first item would be
    } else if (down) {
      nextActive = this._listContainer.firstChild;
    } else {
      nextActive = this._listContainer.lastChild;
    }

    this.setState({
      activeId: nextActive
        ? nextActive.getAttribute('data-suggestion-id')
        : null,
    });
  }

  /**
   * build the DOM structure that makes up
   *  the suggestion box and content containers.
   */
  _renderContentContainers() {
    // container of all suggestion elements
    this._suggestionContainer = document.createElement('div');
    this._suggestionContainer.classList.add(this.options.classNames.container);

    // child elements that will be populated by consumer
    this._header = document.createElement('h4');
    this._header.classList.add(this.options.classNames.header);
    this._setHeader(this.state.header);
    this._suggestionContainer.appendChild(this._header);

    this._listContainer = document.createElement('ul');
    this._listContainer.setAttribute('role', 'listbox');
    this._listContainer.classList.add(this.options.classNames.list);
    this._suggestionContainer.appendChild(this._listContainer);

    // put the suggestions adjacent to the input element
    // firefox does not support insertAdjacentElement
    if (HTMLElement.prototype.insertAdjacentElement) {
      this._input.insertAdjacentElement('afterend', this._suggestionContainer);
    } else {
      // istanbul ignore next
      this._input.parentNode.insertBefore(
        this._suggestionContainer,
        this._input.nextSibling,
      );
    }
  }

  /**
   * updates the content of the list container and builds
   *  the new set of list items.
   */
  _renderListItems() {
    // Create the new list items, render their contents
    // and update the dom with the new elements.

    this._listContainer.innerHTML = '';

    this.state.list.forEach(listItem => {
      const li = document.createElement('li');
      li.setAttribute('role', 'option');
      li.classList.add(this.options.classNames.item);
      li.setAttribute('data-suggestion-id', listItem.__suggestionId);

      // this should use some sort of event delegation if
      // we find we want to expand this to lists with *a lot* of items in it
      // But for now this binding has no real affect on small list perf
      li.addEventListener(
        'mouseenter',
        this._toggleItemHoverState.bind(this, /*hovering*/ true),
      );
      li.addEventListener(
        'mouseleave',
        this._toggleItemHoverState.bind(this, /*hovering*/ false),
      );
      li.addEventListener('mousedown', event => {
        // for situations like mobile, hovering might not be
        // the first event to set the active state for an element
        // so we will mimic that on mouse down and let selection happen
        // at the top level event
        this._toggleItemHoverState(/*hovering*/ true, event);
        this._selectCurrentActiveItem();
      });

      li.innerHTML = this.options.renderListItem(listItem);

      this._listContainer.appendChild(li);
    });
  }

  /**
   * The events that can be set on a "global" or top
   *  level scope, we are going to set them here.
   */
  _addTopLevelEventListeners() {
    // we need to use mousedown instead of click
    // so we can beat the blur event which can
    // change visibility/target of the active event
    document.addEventListener('mousedown', event => {
      const target = event.target;

      // when clicking the input itself or if we are
      // or a global click was made while we were not visible
      // do nothing
      if (!this.state.visible || target === this._input) {
        return;
      }

      // see if inside interaction areas
      if (this._suggestionContainer.contains(target)) {
        event.preventDefault();
        event.stopPropagation();
      }

      // not in an interaction area, so we assume they
      // want it to go away.
      this._toggleSuggestionsVisibility(/*show*/ false);
    });

    // Note, keydown needed here to properly prevent the default
    // nature of navigating keystrokes - like DOWN ARROW at the end of an
    // input takes the cursor to the beginning of the input value.
    this._input.addEventListener(
      'keydown',
      event => {
        const key = event.keyCode;

        // only consume the ENTER event if
        // we have an active item
        if (key === ENTER && !this._getActiveListItemElement()) {
          return;
        }

        // these keys are going to be consumed and not propagated
        if ([ENTER, UP, DOWN].indexOf(key) > -1) {
          if (key === ENTER) {
            this._selectCurrentActiveItem();
          } else {
            this._keyboardSelectionChange(/*down*/ key === DOWN);
          }

          event.preventDefault();
          event.stopPropagation();
          event.stopImmediatePropagation();
        }

        // capture phase needed to beat any other listener that could
        // stop propagation after inspecting input value
      },
      /*useCapturePhase*/ true,
    );

    this._input.addEventListener(
      'keyup',
      event => {
        if ([ENTER, UP, DOWN].indexOf(event.keyCode) === -1) {
          this._filterAndToggleVisibility();
        }

        // capture phase needed to beat any other listener that could
        // stop propagation after inspecting input value
      },
      /*useCapturePhase*/ true,
    );

    this._input.addEventListener('focus', () => {
      this._filterAndToggleVisibility();
    });

    this._input.addEventListener('blur', () => {
      this._toggleSuggestionsVisibility(/*show*/ false);
    });
  }
}
