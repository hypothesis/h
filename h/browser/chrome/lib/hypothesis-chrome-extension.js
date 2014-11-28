(function (h) {
  'use strict';

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
    var help  = new h.HelpPage(chromeTabs, dependencies.extensionURL);
    var store = new h.TabStore(localStorage);
    var state = new h.TabState(store.all(), onTabStateChange);
    var browserAction = new h.BrowserAction(chromeBrowserAction);
    var sidebar = new h.SidebarInjector(chromeTabs, {
      extensionURL: dependencies.extensionURL,
      isAllowedFileSchemeAccess: dependencies.isAllowedFileSchemeAccess,
    });
    var tabErrors = new h.TabErrorCache();

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
      if (changeInfo.status !== 'complete') {
        return;
      }

      if (state.isTabErrored(tabId)) {
        state.restorePreviousState(tabId);
      }

      if (state.isTabActive(tabId)) {
        browserAction.activate(tabId);
      } else {
        browserAction.deactivate(tabId);
      }

      return updateTabDocument(tab);
    }

    function onTabCreated(tab) {
      state.deactivateTab(tab.id);
    }

    function onTabRemoved(tabId) {
      state.clearTab(tabId);
    }

    function updateTabDocument(tab) {
      if (state.isTabActive(tab.id)) {
        return sidebar.injectIntoTab(tab).catch(function (err) {
          tabErrors.setTabError(tab.id, err);
          state.errorTab(tab.id);
        });
      }
      else if (state.isTabInactive(tab.id)) {
        return sidebar.removeFromTab(tab);
      }
    }
  }

  h.HypothesisChromeExtension = HypothesisChromeExtension;
})(window.h || (window.h = {}));
