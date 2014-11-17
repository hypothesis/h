(function (h) {
  'use strict';

  var TabState = h.TabState;
  var icons = {};
  icons[TabState.states.ACTIVE] = {
    19: 'images/browser-icon-active.png',
    38: 'images/browser-icon-active@2x.png'
  };
  icons[TabState.states.INACTIVE] = {
    19: 'images/browser-icon-inactive.png',
    38: 'images/browser-icon-inactive@2x.png'
  };

  // Fake localization function.
  function _(str) {
    return str;
  }

  /* Manages the display of the browser action button. */
  function BrowserAction(chromeBrowserAction) {
    this.setState = function (tabId, state) {
      switch (state) {
        case TabState.states.ACTIVE:   this.activate(tabId); break;
        case TabState.states.INACTIVE: this.deactivate(tabId); break;
        case TabState.states.ERRORED:  this.error(tabId); break;
        default: throw new TypeError('State ' + state + ' is invalid');
      }
    };

    this.activate = function (tabId) {
      chromeBrowserAction.setIcon({tabId: tabId, path: icons[TabState.states.ACTIVE]});
      chromeBrowserAction.setTitle({tabId: tabId, title: _('Hypothesis is active')});
    };

    this.deactivate = function (tabId) {
      chromeBrowserAction.setIcon({tabId: tabId, path: icons[TabState.states.INACTIVE]});
      chromeBrowserAction.setTitle({tabId: tabId, title: _('Hypothesis is inactive')});
    };

    this.error = function (tabId) {
      chromeBrowserAction.setIcon({tabId: tabId, path: icons[TabState.states.INACTIVE]});
      chromeBrowserAction.setTitle({tabId: tabId, title: _('Hypothesis has failed to load')});
      chromeBrowserAction.setBadgeText({tabId: tabId, text: '!'});
    };
  }

  BrowserAction.icons = icons;

  h.BrowserAction = BrowserAction;
})(window.h || (window.h = {}));
