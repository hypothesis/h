'use strict';

var errors = require('./errors');

/* A controller for displaying help pages. These are bound to extension
 * specific errors (found in errors.js) but can also be triggered manually.
 *
 * chromeTabs   - An instance of chrome.tabs.
 * extensionURL - A function that recieves a path and returns a full path
 *   to the file inside the chrome extension. See:
 *   https://developer.chrome.com/extensions/extension#method-getURL
 */
function HelpPage(chromeTabs, extensionURL) {
  /* Accepts an instance of errors.ExtensionError and displays an appropriate
   * help page if one exists.
   *
   * @param {Tab} tab   - The tab to display the error message in.
   * @param {Error} error - The error to display, usually an instance of
   *                        errors.ExtensionError
   */
  this.showHelpForError = function (tab, error) {
    if (error instanceof errors.LocalFileError) {
      return this.showLocalFileHelpPage(tab);
    }
    else if (error instanceof errors.NoFileAccessError) {
      return this.showNoFileAccessHelpPage(tab);
    }
    else if (error instanceof errors.RestrictedProtocolError) {
      return this.showRestrictedProtocolPage(tab);
    }
    else if (error instanceof errors.BlockedSiteError) {
      return this.showBlockedSitePage(tab);
    }
    else {
      return this.showOtherErrorPage(tab, error);
    }
  };

  this.showLocalFileHelpPage = showHelpPage.bind(null, 'local-file');
  this.showNoFileAccessHelpPage = showHelpPage.bind(null, 'no-file-access');
  this.showRestrictedProtocolPage = showHelpPage.bind(null, 'restricted-protocol');
  this.showBlockedSitePage = showHelpPage.bind(null, 'blocked-site');
  this.showOtherErrorPage = showHelpPage.bind(null, 'other-error');

  /**
   * Open a tab displaying the help page.
   *
   * @param {string} helpSection - ID of a <section> within the help page.
   * @param {tabs.Tab} tab - The tab where the error occurred.
   * @param {Error} error - The error which prompted the help page.
   */
  function showHelpPage(helpSection, tab, error) {
    var params = '';
    if (error) {
      params = '?message=' + encodeURIComponent(error.message);
    }

    chromeTabs.create({
      index: tab.index + 1,
      url:  extensionURL('/help/index.html' + params + '#' + helpSection),
      openerTabId: tab.id,
    });
  }
}

module.exports = HelpPage;
