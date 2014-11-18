(function (h) {
  'use strict';

  function HypothesisChromeExtension(options) {
    var chromeTabs = options.chromeTabs;
    var chromeBrowserAction = options.chromeBrowserAction;
    var help  = new h.HelpPage(chromeTabs, options.extensionURL);
    var store = new h.TabStore(localStorage);
    var state = new h.TabState(store.all(), onTabStateChange);
    var browserAction = new h.BrowserAction(chromeBrowserAction);
    var sidebar = new h.SidebarInjector(chromeTabs, {
      extensionURL: options.extensionURL,
      isAllowedFileSchemeAccess: options.isAllowedFileSchemeAccess,
    });
    var tabErrors = new h.TabErrorCache();

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
    };

    function onBrowserActionClicked(tab) {
      var tabError = tabErrors.getTabError(tab.id);
      if (state.isTabErrored(tab.id) && tabError) {
        help.showHelpForError(tab.id, tabError);
      }
      else if (state.isTabActive(tab.id)) {
        state.deactivateTab(tab.id);
      }
      else {
        state.activateTab(tab.id);
      }
    };

    function onTabUpdated(tabId, changeInfo, tab) {
      if (state.isTabErrored(tabId)) {
        state.restorePreviousState(tabId);
      }

      if (state.isTabActive(tabId)) {
        browserAction.activate(tabId);
      } else {
        browserAction.deactivate(tabId);
      }

      updateTabDocument(tab);
    }

    function onTabCreated(tab) {
      state.deactivateTab(tab.id);
    }

    function onTabRemoved(tabId) {
      state.clearTab(tabId);
    }

    function updateTabDocument(tab) {
      if (state.isTabActive(tab.id)) {
        sidebar.injectIntoTab(tab, function (err) {
          if (err) {
            tabErrors.setTabError(tab.id, err);
            state.errorTab(tab.id);
          }
        });
      }
      else if (state.isTabInactive(tab.id)) {
        sidebar.removeFromTab(tab);
      }
    }
  }

  h.HypothesisChromeExtension = HypothesisChromeExtension;
})(window.h || (window.h = {}));
