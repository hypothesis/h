(function (h) {
  'use strict';

  var states = {
    ACTIVE:   'active',
    INACTIVE: 'inactive',
    ERRORED:  'errored',
  };

  /* Manages the state of the browser action button to ensure that it displays
   * correctly for the currently active tab.
   */
  function TabState(initialState, onchange) {
    var currentState;
    var previousState;

    this.onchange = onchange || null;

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
