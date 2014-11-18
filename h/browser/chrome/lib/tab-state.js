(function (h) {
  'use strict';

  var states = {
    ACTIVE:   'active',
    INACTIVE: 'inactive',
    ERRORED:  'errored',
  };

  /* Manages the state of the browser action button to ensure that it displays
   * correctly for the currently active tab. An onchange callback will be
   * called when the extension changes state. This will be provided
   * with the tabId, the current and previous states.
   *
   * Each state has a method to enable it such as activateTab() and a method
   * to query the current state such as isTabActive().
   *
   * initialState - An Object of tabId/state keys. Ideal for loading state
   *   from a persisted store such as local storage.
   * onchange     - A function that recieves onchange(tabId, current, prev).
   */
  function TabState(initialState, onchange) {
    var currentState;
    var previousState;

    this.onchange = onchange || null;

    /* Replaces the entire state of the object with a new one.
     *
     * newState - An object of tabId/state pairs.
     *
     * Returns nothing.
     */
    this.load = function (newState) {
      previousState = currentState || {};
      currentState = newState;
    };

    this.activateTab = function (tabId) {
      transition(tabId, states.ACTIVE, this.onchange);
    };

    this.deactivateTab = function (tabId) {
      transition(tabId, states.INACTIVE, this.onchange);
    };

    this.errorTab = function (tabId) {
      transition(tabId, states.ERRORED, this.onchange);
    };

    this.clearTab = function (tabId) {
      transition(tabId, null, this.onchange);
    };

    this.restorePreviousState = function (tabId) {
      transition(tabId, previousState[tabId], this.onchange);
    };

    this.isTabActive = function (tabId) {
      return currentState[tabId] === states.ACTIVE;
    };

    this.isTabInactive = function (tabId) {
      return currentState[tabId] === states.INACTIVE;
    };

    this.isTabErrored = function (tabId) {
      return currentState[tabId] === states.ERRORED;
    };

    function transition (tabId, state, fn) {
      previousState[tabId] = currentState[tabId];
      currentState[tabId] = state;
      if (typeof fn === 'function') {
        fn(tabId, state, previousState[tabId] || null);
      }
    }

    this.load(initialState || {});
  }

  TabState.states = states;

  h.TabState = TabState;
})(window.h || (window.h = {}));
