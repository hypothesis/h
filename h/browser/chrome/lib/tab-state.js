'use strict';

var assign = require('core-js/modules/$.assign');
var isShallowEqual = require('is-equal-shallow');

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
    this.setState(tabId, {state: states.ACTIVE}, options);
  };

  this.deactivateTab = function (tabId, options) {
    this.setState(tabId, {state: states.INACTIVE}, options);
  };

  this.errorTab = function (tabId, options) {
    this.setState(tabId, {state: states.ERRORED}, options);
  };

  this.clearTab = function (tabId) {
    this.setState(tabId, null);
  };

  this.restorePreviousState = function (tabId) {
    this.setState(tabId, previousState[tabId], this.onchange);
  };

  function getState(tabId) {
    if (!currentState[tabId]) {
      return {
        state: states.INACTIVE,
        annotationCount: 0,
      };
    }
    return currentState[tabId];
  }

  this.getState = getState;

  this.annotationCount = function(tabId) {
    return getState(tabId).annotationCount;
  }

  this.isTabActive = function (tabId) {
    return getState(tabId).state === states.ACTIVE;
  };

  this.isTabInactive = function (tabId) {
    return getState(tabId).state === states.INACTIVE;
  };

  this.isTabErrored = function (tabId) {
    return getState(tabId).state === states.ERRORED;
  };

  /**
   * Updates the H state for a tab.
   *
   * @param tabId - The ID of the tab being updated
   * @param stateUpdate - A dictionary of {key:value} properties for
   *                      state properties to update.
   * @param options - The 'force' option allows the caller to re-trigger
   *                  an onchange event for the current state without modifying
   *                  the previous state. This is useful for restoring tab state
   *                  after the extension is reloaded.
   */
  this.setState = function (tabId, stateUpdate, options) {
    var newState;
    if (stateUpdate) {
      newState = assign({
        // default state
        state: states.INACTIVE,
      }, currentState[tabId], stateUpdate);
    }

    var isForced = !!options && options.force === true;
    var hasChanged = !isShallowEqual(newState, currentState[tabId]);
    if (!isForced && !hasChanged) { return; }

    if (!isForced || hasChanged) {
      previousState[tabId] = currentState[tabId];
      currentState[tabId] = newState;
    }

    if (typeof _this.onchange === 'function') {
      _this.onchange(tabId, newState, previousState[tabId] || null);
    }
  }

  /**
   * Query the server for the annotation count for a URL
   * and update the annotation count for the tab accordingly.
   *
   * @method
   * @param {integer} tabId The id of the tab.
   * @param {string} tabUrl The URL of the tab.
   * @param {string} apiUrl The URL of the Hypothesis API.
   */
  this.updateAnnotationCount = function(tabId, tabUrl, apiUrl) {
    // Fetch the number of annotations of the current page from the server,
    // and display it as a badge on the browser action button.
    var self = this;
    var xhr = new XMLHttpRequest();
    xhr.onload = function() {
      var total;

      try {
        total = JSON.parse(this.response).total;
      } catch (e) {
        console.error(
          'updateAnnotationCount() received invalid JSON from the server: ' + e);
        return;
      }

      if (typeof total !== 'number') {
        console.error('annotation count is not a number');
        return;
      }

      self.setState(tabId, {annotationCount: total});
    };

    xhr.open('GET', apiUrl + '/badge?uri=' + tabUrl);
    xhr.send();
  };

  this.load(initialState || {});
}

TabState.states = states;

module.exports = TabState;
