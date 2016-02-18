'use strict';

var errors = require('./errors');
var TabState = require('./tab-state');
var BrowserAction = require('./browser-action');
var HelpPage = require('./help-page');
var SidebarInjector = require('./sidebar-injector');
var TabStore = require('./tab-store');

var TAB_STATUS_LOADING = 'loading';
var TAB_STATUS_COMPLETE = 'complete';

/* The main extension application. This wires together all the smaller
 * modules. The app listens to all new created/updated/removed tab events
 * and uses the TabState object to keep track of whether the sidebar is
 * active or inactive in the tab. The app also listens to click events on
 * the browser action and toggles the state and uses the BrowserAction module
 * to update the visual style of the button.
 *
 * The SidebarInjector handles the insertion of the Hypothesis code. If it
 * runs into errors the tab is put into an errored state and when the
 * browser action is clicked again the HelpPage module displays more
 * information to the user.
 *
 * Lastly the TabStore listens to changes to the TabState module and persists
 * the current settings to localStorage. This is then loaded into the
 * application on startup.
 *
 * Relevant Chrome Extension documentation:
 * - https://developer.chrome.com/extensions/browserAction
 * - https://developer.chrome.com/extensions/tabs
 * - https://developer.chrome.com/extensions/extension
 *
 * dependencies - An object to set up the application.
 *   chromeTabs: An instance of chrome.tabs.
 *   chromeBrowserAction: An instance of chrome.browserAction.
 *   extensionURL: chrome.extension.getURL.
 *   isAllowedFileSchemeAccess: chrome.extension.isAllowedFileSchemeAccess.
 */
function HypothesisChromeExtension(dependencies) {
  var chromeTabs = dependencies.chromeTabs;
  var chromeBrowserAction = dependencies.chromeBrowserAction;
  var help  = new HelpPage(chromeTabs, dependencies.extensionURL);
  var store = new TabStore(localStorage);
  var state = new TabState(store.all(), onTabStateChange);
  var browserAction = new BrowserAction(chromeBrowserAction);
  var sidebar = new SidebarInjector(chromeTabs, {
    extensionURL: dependencies.extensionURL,
    isAllowedFileSchemeAccess: dependencies.isAllowedFileSchemeAccess,
  });

  restoreSavedTabState();

  /* Sets up the extension and binds event listeners. Requires a window
   * object to be passed so that it can listen for localStorage events.
   */
  this.listen = function (window) {
    chromeBrowserAction.onClicked.addListener(onBrowserActionClicked);
    chromeTabs.onCreated.addListener(onTabCreated);

    // when a user navigates within an existing tab,
    // onUpdated is fired in most cases
    chromeTabs.onUpdated.addListener(onTabUpdated);

    // ... but when a user navigates to a page that is loaded
    // via prerendering or instant results, onTabReplaced is
    // fired instead. See https://developer.chrome.com/extensions/tabs#event-onReplaced
    // and https://code.google.com/p/chromium/issues/detail?id=109557
    chromeTabs.onReplaced.addListener(onTabReplaced);

    chromeTabs.onRemoved.addListener(onTabRemoved);
  };

  /* A method that can be used to setup the extension on existing tabs
   * when the extension is re-installed.
   */
  this.install = function () {
    restoreSavedTabState();
  };

  /* Opens the onboarding page */
  this.firstRun = function (extensionInfo) {
    // If we've been installed because of an administrative policy, then don't
    // open the welcome page in a new tab.
    //
    // It's safe to assume that if an admin policy is responsible for installing
    // the extension, opening the welcome page is going to do more harm than
    // good, as it will appear that a tab opened without user action.
    //
    // See:
    //
    //   https://developer.chrome.com/extensions/management#type-ExtensionInstallType
    //
    if (extensionInfo.installType === 'admin') {
      return;
    }

    chromeTabs.create({url: 'https://hypothes.is/welcome'}, function (tab) {
      state.activateTab(tab.id);
    });
  };

  function restoreSavedTabState() {
    store.reload();
    state.load(store.all());
    chromeTabs.query({}, function (tabs) {
      tabs.forEach(function (tab) {
        onTabStateChange(tab.id, state.getState(tab.id));
      });
    });
  }

  function onTabStateChange(tabId, current) {
    if (current) {
      browserAction.update(tabId, current);
      chromeTabs.get(tabId, updateTabDocument);

      if (!state.isTabErrored(tabId)) {
        store.set(tabId, current);
      }
    } else {
      store.unset(tabId);
    }
  }

  // exposed for use by tests
  this._onTabStateChange = onTabStateChange;

  function onBrowserActionClicked(tab) {
    var tabError = state.getState(tab.id).error;
    if (tabError) {
      help.showHelpForError(tab, tabError);
    }
    else if (state.isTabActive(tab.id)) {
      state.deactivateTab(tab.id);
    }
    else {
      state.activateTab(tab.id);
    }
  }

  /**
   * Returns the active state for a tab
   * which has just been navigated to.
   */
  function activeStateForNavigatedTab(tabId) {
    var activeState = state.getState(tabId).state;
    if (activeState === TabState.states.ERRORED) {
      // user had tried to activate H on the previous page but it failed,
      // retry on the new page
      activeState = TabState.states.ACTIVE;
    }
    return activeState;
  }

  function resetTabState(tabId, url) {
    state.setState(tabId, {
      state: activeStateForNavigatedTab(tabId),
      ready: false,
      annotationCount: 0,
      extensionSidebarInstalled: false,
    });
    state.updateAnnotationCount(tabId, url);
  }

  // This function will be called multiple times as the tab reloads.
  // https://developer.chrome.com/extensions/tabs#event-onUpdated
  //
  // 'changeInfo' contains details of what changed about the tab's status.
  // Two important events are when the tab's `status` changes to `loading`
  // when the user begins a new navigation and when the tab's status changes
  // to `complete` after the user completes a navigation
  function onTabUpdated(tabId, changeInfo, tab) {
    if (changeInfo.status === TAB_STATUS_LOADING) {
      resetTabState(tabId, tab.url);
    } else if (changeInfo.status === TAB_STATUS_COMPLETE) {
      state.setState(tabId, {
        ready: true,
      });
    }
  }

  function onTabReplaced(addedTabId, removedTabId) {
    state.setState(addedTabId, {
      state: activeStateForNavigatedTab(removedTabId),
      ready: true,
    });
    state.clearTab(removedTabId);

    chromeTabs.get(addedTabId, function (tab) {
      state.updateAnnotationCount(addedTabId, tab.url);
    });
  }

  function onTabCreated(tab) {
    // Clear the state in case there is old, conflicting data in storage.
    state.clearTab(tab.id);
  }

  function onTabRemoved(tabId) {
    state.clearTab(tabId);
  }

  // installs or uninstalls the sidebar from a tab when the H
  // state for a tab changes
  function updateTabDocument(tab) {
    // If the tab has not yet finished loading then just quietly return.
    if (!state.getState(tab.id).ready) {
      return Promise.resolve();
    }

    var isInstalled = state.getState(tab.id).extensionSidebarInstalled;
    if (state.isTabActive(tab.id) && !isInstalled) {
      // optimistically set the state flag indicating that the sidebar
      // has been installed
      state.setState(tab.id, {
        extensionSidebarInstalled: true,
      });
      return sidebar.injectIntoTab(tab)
        .catch(function (err) {
          errors.report(err, 'Injecting Hypothesis sidebar', {
            url: tab.url,
          });
          state.errorTab(tab.id, err);
        });
    }
    else if (state.isTabInactive(tab.id) && isInstalled) {
      return sidebar.removeFromTab(tab).then(function () {
        state.setState(tab.id, {
          extensionSidebarInstalled: false,
        });
      });
    }
  }
}

module.exports = HypothesisChromeExtension;
