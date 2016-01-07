'use strict';

var assign = require('core-js/modules/$.object-assign');
var isShallowEqual = require('is-equal-shallow');

var states = {
  ACTIVE:   'active',
  INACTIVE: 'inactive',
  ERRORED:  'errored',
};

/** The default H state for a new browser tab */
var DEFAULT_STATE = {
  /** Whether or not H is active on the page */
  state: states.INACTIVE,
  /** The count of annotations on the page visible to the user,
   * as returned by the badge API
   */
  annotationCount: 0,
  /** Whether or not the H sidebar has been installed onto the page by
   * the extension
   */
  extensionSidebarInstalled: false,
  /** Whether the tab is loaded and ready for the sidebar to be installed. */
  ready: false,
  /** The error for the current tab. */
  error: undefined,
};

/** encodeUriQuery encodes a string for use in a query parameter */
function encodeUriQuery(val) {
  return encodeURIComponent(val).replace(/%20/g, '+');
}

/** TabState stores the H state for a tab. This state includes:
 *
 * - Whether the extension has been activated on a tab
 * - Whether the sidebar is currently installed on a tab
 * - The count of annotations visible to the user on the URL currently
 *   displayed in the tab.
 *
 * The H state for a tab is updated via the setState() method and
 * retrieved via getState().
 *
 * When the H state for a tab changes, the `onchange()` callback will
 * be triggered with the tab ID and current and previous states.
 *
 * initialState - An Object of tabId/state keys. Used when loading state
 *   from a persisted store such as localStorage. This will be merged with
 *   the default state for a tab.
 * onchange     - A function that recieves onchange(tabId, current).
 */
function TabState(initialState, onchange) {
  var _this = this;
  var currentState;

  this.onchange = onchange || null;

  /** Replaces the H state for all tabs with the state data
   * from `newState`.
   *
   * @param newState - A dictionary mapping tab ID to tab state objects.
   *                   The provided state will be merged with the default
   *                   state for a tab.
   */
  this.load = function (newState) {
    var newCurrentState = {};
    Object.keys(newState).forEach(function (tabId) {
      newCurrentState[tabId] = assign({}, DEFAULT_STATE, newState[tabId]);
    });
    currentState = newCurrentState;
  };

  this.activateTab = function (tabId) {
    this.setState(tabId, {state: states.ACTIVE});
  };

  this.deactivateTab = function (tabId) {
    this.setState(tabId, {state: states.INACTIVE});
  };

  this.errorTab = function (tabId, error) {
    this.setState(tabId, {
      state: states.ERRORED,
      error: error,
    });
  };

  this.clearTab = function (tabId) {
    this.setState(tabId, null);
  };

  this.getState = function (tabId) {
    if (!currentState[tabId]) {
      return DEFAULT_STATE;
    }
    return currentState[tabId];
  };

  this.annotationCount = function(tabId) {
    return this.getState(tabId).annotationCount;
  }

  this.isTabActive = function (tabId) {
    return this.getState(tabId).state === states.ACTIVE;
  };

  this.isTabInactive = function (tabId) {
    return this.getState(tabId).state === states.INACTIVE;
  };

  this.isTabErrored = function (tabId) {
    return this.getState(tabId).state === states.ERRORED;
  };

  /**
   * Updates the H state for a tab.
   *
   * @param tabId - The ID of the tab being updated
   * @param stateUpdate - A dictionary of {key:value} properties for
   *                      state properties to update or null if the
   *                      state should be removed.
   */
  this.setState = function (tabId, stateUpdate) {
    var newState;
    if (stateUpdate) {
      newState = assign({}, this.getState(tabId), stateUpdate);
      if (newState.state !== states.ERRORED) {
        newState.error = undefined;
      }
    }

    if (isShallowEqual(newState, currentState[tabId])) {
      return;
    }

    currentState[tabId] = newState;

    if (_this.onchange) {
      _this.onchange(tabId, newState);
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

    xhr.open('GET', apiUrl + '/badge?uri=' + encodeUriQuery(tabUrl));
    xhr.send();
  };

  this.load(initialState || {});
}

TabState.states = states;

module.exports = TabState;
