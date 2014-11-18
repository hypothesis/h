(function (h) {
  'use strict';

  /* A controller for displaying help pages. These are bound to extension
   * specific errors (found in errors.js) but can also be triggered manually.
   *
   * chromeTabs   - An instance of chrome.tabs.
   * extensionURL - A function that recieves a path and returns a full path
   *   to the file inside the chrome extension. See:
   *   https://developer.chrome.com/extensions/extension#method-getURL
   */
  function HelpPage(chromeTabs, extensionURL) {
    /* Accepts an instance of h.ExtensionError and displays an appropriate
     * help page if one exists.
     *
     * tab   - The tab to display the error message in.
     * error - An instance of h.ExtensionError.
     *
     * Throws an error if no page is available for the action.
     * Returns nothing.
     */
    this.showHelpForError = function (tab, error) {
      if (error instanceof h.LocalFileError) {
        return this.showLocalFileHelpPage(tab);
      }
      else if (error instanceof h.NoFileAccessError) {
        return this.showNoFileAccessHelpPage(tab);
      }

      throw new Error('showHelpForError does not support the error: ' + error.message);
    };

    this.showLocalFileHelpPage = showHelpPage.bind(null, 'local-file');
    this.showNoFileAccessHelpPage = showHelpPage.bind(null, 'no-file-access');

    // Render the help page. The helpSection should correspond to the id of a
    // section within the help page.
    function showHelpPage(helpSection, tab) {
      chromeTabs.update(tab.id, {
        url:  extensionURL('/help/permissions.html#' + helpSection)
      });
    }
  }

  h.HelpPage = HelpPage;
})(window.h || (window.h = {}));
