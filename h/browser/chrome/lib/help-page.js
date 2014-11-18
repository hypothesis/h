(function (h) {
  'use strict';

  function HelpPage(chromeTabs, extensionURL) {
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
