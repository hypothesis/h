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
 * initialState - An Object of tabId/state keys. Used when loading state
 *   from a persisted store such as localStorage.
 * onchange     - A function that recieves onchange(tabId, current, prev).
 */
function TabState(initialState, onchange) {
  var _this = this;
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

  this.activateTab = function (tabId, options) {
    transition(tabId, states.ACTIVE, options);
  };

  this.deactivateTab = function (tabId, options) {
    transition(tabId, states.INACTIVE, options);
  };

  this.errorTab = function (tabId, options) {
    transition(tabId, states.ERRORED, options);
  };

  this.clearTab = function (tabId) {
    transition(tabId, null);
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

  // options.force allows the caller to re-trigger an onchange event for
  // the current state without modifying the previous state. This is useful
  // for restoring tab state after the extension is reloaded.
  function transition (tabId, state, options) {
    var isForced = !!options && options.force === true;
    var hasChanged = state !== currentState[tabId];
    if (!isForced && !hasChanged) { return; }

    if (!isForced || hasChanged) {
      previousState[tabId] = currentState[tabId];
      currentState[tabId] = state;
    }

    if (typeof _this.onchange === 'function') {
      _this.onchange(tabId, state, previousState[tabId] || null);
    }
  }

  this.load(initialState || {});
}

TabState.states = states;

module.exports = TabState;
