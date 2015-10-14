'use strict';

var TabState = require('./tab-state');
var BrowserAction = require('./browser-action');
var HelpPage = require('./help-page');
var SidebarInjector = require('./sidebar-injector');
var TabErrorCache = require('./tab-error-cache');
var TabStore = require('./tab-store');
var uriInfo = require('./uri-info');
var errors = require('./errors');

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
 * browser aciton is clicked again the HelpPage module displays more
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
  var tabErrors = new TabErrorCache();

  /* Sets up the extension and binds event listeners. Requires a window
   * object to be passed so that it can listen for localStorage events.
   */
  this.listen = function (window) {
    chromeBrowserAction.onClicked.addListener(onBrowserActionClicked);
    chromeTabs.onCreated.addListener(onTabCreated);
    chromeTabs.onUpdated.addListener(onTabUpdated);
    chromeTabs.onRemoved.addListener(onTabRemoved);

    // FIXME: Find out why we used to reload the data on every get.
    window.addEventListener('storage', function (event) {
      var key = 'state';
      var isState = event.key === key;
      var isUpdate = event.newValue !== null;

      // Check the event is for the store and check that something has
      // actually changed externally by validating the new value.
      if (isState && isUpdate && event.newValue !== JSON.stringify(store.all())) {
        store.reload();
        state.load(store.all());
      }
    });
  };

  /* A method that can be used to setup the extension on existing tabs
   * when the extension is installed.
   */
  this.install = function () {
    chromeTabs.query({}, function (tabs) {
      tabs.forEach(function (tab) {
        if (state.isTabActive(tab.id)) {
          state.activateTab(tab.id, {force: true});
        } else {
          state.deactivateTab(tab.id, {force: true});
        }
      });
    });
  };

  /* Opens the onboarding page */
  this.firstRun = function () {
    chromeTabs.create({url: 'https://hypothes.is/welcome'}, function (tab) {
      state.activateTab(tab.id);
    });
  };

  function onTabStateChange(tabId, current, previous) {
    if (current) {
      browserAction.setState(tabId, current);

      if (!state.isTabErrored(tabId)) {
        store.set(tabId, current);
        tabErrors.unsetTabError(tabId);
        chromeTabs.get(tabId, updateTabDocument);
      }
    } else {
      store.unset(tabId);
      tabErrors.unsetTabError(tabId);
    }
  }

  // exposed for use by tests
  this._onTabStateChange = onTabStateChange;

  function onBrowserActionClicked(tab) {
    var tabError = tabErrors.getTabError(tab.id);
    if (state.isTabErrored(tab.id) && tabError) {
      help.showHelpForError(tab, tabError);
    }
    else if (state.isTabActive(tab.id)) {
      state.deactivateTab(tab.id);
    }
    else {
      state.activateTab(tab.id);
    }
  }

  function onTabUpdated(tabId, changeInfo, tab) {
    // This function will be called multiple times as the tab reloads.
    // https://developer.chrome.com/extensions/tabs#event-onUpdated
    if (changeInfo.status !== TAB_STATUS_COMPLETE) {
      return Promise.resolve();
    }

    if (state.isTabErrored(tabId)) {
      state.restorePreviousState(tabId);
    }

    if (state.isTabActive(tabId)) {
      browserAction.activate(tabId);
    } else {
      // Clear the state to express that the user has no preference.
      // This allows the publisher embed to persist without us destroying it.
      state.clearTab(tabId);
      browserAction.deactivate(tabId);
    }

    // Here we're calling uriInfo.get() for two reasons:
    // 1. Because we want to call updateBadge() in the then() function.
    // 2. Because we want to fetch the info for the new URL asap, when we
    //    call uriInfo.get() again later (when the user clicks on the browser
    //    button to activate the sidebar) it will return the already-resolved
    //    Promise.
    uriInfo(tab.url).then(function(info) {
      if (!info.blocked) {
        browserAction.updateBadge(info.total, tab.id);
      }
    }).
    catch(function() {
      // Silence console error message about uncaught exception here.
    });
    return updateTabDocument(tab);
  }

  function onTabCreated(tab) {
    // Clear the state in case there is old, conflicting data in storage.
    state.clearTab(tab.id);
  }

  function onTabRemoved(tabId) {
    state.clearTab(tabId);
  }

  function updateTabDocument(tab) {
    // If the tab has not yet finished loading then just quietly return.
    if (tab.status !== TAB_STATUS_COMPLETE) {
      return Promise.resolve();
    }

    function inject(tab) {
      sidebar.injectIntoTab(tab).catch(function (err) {
        tabErrors.setTabError(tab.id, err);
        state.errorTab(tab.id);
      });
    }

    if (state.isTabActive(tab.id)) {
      return uriInfo(tab.url).then(
        function onFulfilled(info) {
          if (info.blocked) {
              tabErrors.setTabError(
                tab.id, new errors.BlockedSiteError(
                  "Hypothesis doesn't work on this site yet."));
              state.errorTab(tab.id);
          } else {
            inject(tab);
          }
        },
        function onRejected() {
          // If the request to the server to get the uriinfo times out or
          // fails for any reason, then we just assume that the URI isn't
          // blocked and go ahead and inject the sidebar.
          inject(tab);
        });
    } else if (state.isTabInactive(tab.id)) {
      return sidebar.removeFromTab(tab);
    }
    return Promise.resolve();
  }
}

module.exports = HypothesisChromeExtension;
