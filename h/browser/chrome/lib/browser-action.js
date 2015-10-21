'use strict';

var settings = require('./settings');
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

var buildType = '';
settings.then(function (settings) {
  buildType = settings.buildType;
}).catch(function (err) {
  console.error(err);
});

// themes to apply to the toolbar icon badge depending on the type of
// build. Production builds use the default color and no text
var badgeThemes = {
  'dev': {
    defaultText: 'DEV',
    color: '#5BCF59', // Emerald green
  },
  'staging': {
    defaultText: 'STG',
    color: '#EDA061', // Porche orange-pink
  }
};

// Fake localization function.
function _(str) {
  return str;
}

/* Controls the display of the browser action button setting the icon, title
 * and badges depending on the current state of the tab.
 *
 * BrowserAction is responsible for mapping the logical H state of
 * a tab (whether the extension is active, annotation count) to
 * the badge state.
 */
function BrowserAction(chromeBrowserAction) {
  /**
   * Updates the state of the browser action to reflect the logical
   * H state of a tab.
   *
   * @param state - The H state of a tab. See the 'tab-state' module.
   */
  this.update = function(tabId, state) {
    var activeIcon = icons[states.INACTIVE];
    var title = '';
    var badgeText = '';

    if (state.state === states.ACTIVE) {
      activeIcon = icons[states.ACTIVE];
      title = 'Hypothesis is active';
    } else if (state.state === states.INACTIVE) {
      title = 'Hypothesis is inactive';
    } else if (state.state === states.ERRORED) {
      title = 'Hypothesis failed to load';
      badgeText = '!';
    } else {
      throw new Error('Unknown tab state');
    }

    // display the annotation count on the badge
    if (state.state !== states.ERRORED && state.annotationCount) {
      var countLabel;
      var totalString = state.annotationCount.toString();
      if (state.annotationCount > 999) {
        totalString = '999+';
      }
      if (state.annotationCount === 1) {
        countLabel = _("There's 1 annotation on this page");
      } else {
        countLabel = _('There are ' + totalString + ' annotations on ' +
                  'this page');
      }
      title = countLabel;
      badgeText = totalString;
    }

    // update the badge style to reflect the build type
    var badgeTheme = badgeThemes[buildType];
    if (badgeTheme) {
      chromeBrowserAction.setBadgeBackgroundColor({
        tabId: tabId,
        color: badgeTheme.color,
      });
      if (!badgeText) {
        badgeText = badgeTheme.defaultText;
      }
    }

    chromeBrowserAction.setBadgeText({tabId: tabId, text: badgeText});
    chromeBrowserAction.setIcon({tabId: tabId, path: activeIcon});
    chromeBrowserAction.setTitle({tabId: tabId, title: title});
  }
}

BrowserAction.icons = icons;

module.exports = BrowserAction;
