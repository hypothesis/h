'use strict';

var TabState = require('./tab-state');

// Cache the tab state constants.
var states = TabState.states;

// Each button state has two icons one for normal resolution (19) and one
// for hi-res screens (38).
var icons = {};
icons[states.ACTIVE] = {
  19: 'images/browser-icon-active.png',
  38: 'images/browser-icon-active@2x.png'
};
icons[states.INACTIVE] = {
  19: 'images/browser-icon-inactive.png',
  38: 'images/browser-icon-inactive@2x.png'
};

// Fake localization function.
function _(str) {
  return str;
}

/* Controls the display of the browser action button setting the icon, title
 * and badges depending on the current state of the tab. This is a stateless
 * module and does not store the current state. A TabState instance should
 * be used to manage which tabs are active/inactive.
 */
function BrowserAction(chromeBrowserAction) {
  this.setState = function (tabId, state) {
    switch (state) {
      case states.ACTIVE:   this.activate(tabId); break;
      case states.INACTIVE: this.deactivate(tabId); break;
      case states.ERRORED:  this.error(tabId); break;
      default: throw new TypeError('State ' + state + ' is invalid');
    }
  };

  /**
   * Set the "title" (tooltip) of the browser action _if_ no badge is
   * currently displayed on the browser action.
   * @param {integer} tabId The id of the tab to set the badge title for.
   * @param {string} title The value to set the title to.
   */
  function setTitleIfNoBadge(tabId, title) {
    chromeBrowserAction.getBadgeText({tabId: tabId}, function(text) {
      if (!text) {
        chromeBrowserAction.setTitle({tabId: tabId, title: title});
      }
    });
  }

  /**
   * Set the "title" (tooltip) and badge text of the browser action.
   * @param {integer} tabId The id of the tab to set the badge title for.
   * @param {string} title The text to show in the tooltip.
   * @param {string} badgeText The text to show on the badge.
   */
  function setTitleAndBadgeText(tabId, title, badgeText) {
    chromeBrowserAction.setTitle({tabId: tabId, title: title});
    chromeBrowserAction.setBadgeText({tabId: tabId, text: badgeText});
  }

  /* Sets the active browser action appearance for the provided tab id. */
  this.activate = function(tabId) {
    chromeBrowserAction.setIcon({tabId: tabId, path: icons[states.ACTIVE]});
    setTitleIfNoBadge(tabId, _('Hypothesis is active'));
  };

  /* Sets the inactive browser action appearance for the provided tab id. */
  this.deactivate = function(tabId) {
    chromeBrowserAction.setIcon({tabId: tabId, path: icons[states.INACTIVE]});
    setTitleIfNoBadge(tabId, _('Hypothesis is inactive'));
  };

  /* Sets the errored browser action appearance for the provided tab id. */
  this.error = function(tabId) {
    chromeBrowserAction.setIcon({tabId: tabId, path: icons[states.INACTIVE]});
    setTitleAndBadgeText(tabId,  _('Hypothesis has failed to load'), '!');
  };

  /**
    * Show the number of annotations of the current page in the badge.
    *
    * @method
    * @param {Number} total The number of annotations to show on the badge
    * @param {Number} tabId The id of the current tab.
    */
  this.updateBadge = function(total, tabId) {
    if (total < 1) {
      return;
    }
    var totalString = total.toString();
    if (total > 999) {
      totalString = '999+';
    }
    chromeBrowserAction.getBadgeText({tabId: tabId}, function(text) {
      // The num. annotations badge is low priority - we only set it if
      // there's no other badge currently showing.
      if (!text) {
        var title;
        if (total === 1) {
          title = _("There's 1 annotation on this page");
        } else {
          title = _('There are ' + totalString + ' annotations on ' +
                  'this page');
        }
        setTitleAndBadgeText(tabId, title, totalString);
      }
    });
  };
}

BrowserAction.icons = icons;

module.exports = BrowserAction;
