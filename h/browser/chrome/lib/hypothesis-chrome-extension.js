(function (h) {
  'use strict';

  function HypotheisChromeExtension(options) {
    var chromeTabs = options.chromeTabs;
    var chromeBrowserAction = options.chromeBrowserAction;
    var store = new h.TabStore(localStorage);
    var state = new h.TabState(store.all(), onTabStateChange);
    var browserAction = new h.BrowserAction(chromeBrowserAction);
    var sidebar = new h.SidebarInjector(chromeTabs, {
      extensionURL: options.extensionURL,
      isAllowedFileSchemeAccess: options.isAllowedFileSchemeAccess,
    });

    this.listen = function (window) {
      chromeBrowserAction.onClicked.addListener(onBrowserActionClicked);
      chromeTabs.onCreated.addListener(onTabCreated)
      chromeTabs.onUpdated.addListener(onTabUpdated)
      chromeTabs.onRemoved.addListener(onTabRemoved)

      window.addEventListener('storage', function (event) {
        if (event.key === 'state' && event.newValue !== null) {
          store.reload();
          state.load(store.all());
        }
      });
    };

    this.install = function () {
      chromeTabs.query({}, function (tabs) {
        tabs.forEach(function (tab) {
          if (state.isTabActive(tab.id)) {
            state.activateTab(tab.id);
          } else {
            state.deactivateTab(tab.id);
          }
        });
      });
    };

    function onTabStateChange(tabId, current, previous) {
      browserAction.setState(tabId, current);
      if (!state.isTabErrored(tabId)) {
        store.set(tabId, current);
        chromeTabs.get(tabId, updateTabDocument);
      }
    };

    function onBrowserActionClicked(tab) {
      if (state.isTabErrored(tab.id)) {
        // Show Help
      }
      else if (state.isTabActive(tab.id)) {
        state.deactivateTab(tab.id);
      }
      else {
        state.activateTab(tab.id);
      }
    };

    function onTabUpdated(tab) {
      if (state.isTabErrored(tab.id)) {
        state.restorePreviousState(tab.id);
      }
      updateTabDocument(tab);
    }

    function onTabCreated(tab) {
      state.deactivateTab(tab.id);
    }

    function onTabRemoved(tab) {
      state.clearTab(tab.id);
    }

    function updateTabDocument(tab) {
      if (state.isTabActive(tab.id)) {
        sidebar.injectIntoTab(tab);
      }
      else if (state.isTabInactive(tab.id)) {
        sidebar.removeFromTab(tab);
      }
    }
  }

  h.HypotheisChromeExtension = HypotheisChromeExtension;
})(window.h || (window.h = {}));
