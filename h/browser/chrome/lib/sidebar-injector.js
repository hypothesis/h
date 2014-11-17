(function (h) {
  'use strict';

  function SidebarInjector(chromeTabs, options) {
    options = options || {};

    var isAllowedFileSchemeAccess = options.isAllowedFileSchemeAccess;
    var extensionURL = options.extensionURL;

    if (typeof extensionURL !== 'function') {
      throw new TypeError('createURL must be a function');
    }

    if (typeof isAllowedFileSchemeAccess !== 'function') {
      throw new TypeError('isAllowedFileSchemeAccess must be a function');
    }

    this.injectIntoTab = function (tab, fn) {
      fn = fn || function () {};

      if (isChromeURL(tab.url)) {
        return setTimeout(fn.bind(null, null));
      }

      injectConfig(tab, function () {
        function checkPDF(success, fallback) {
          if (isPDFURL(tab.url)) {
            success(tab, fn);
          } else {
            fallback(tab, fn);
          }
        }

        if (isFileURL(tab.url)) {
          if (isPDFURL(tab.url)) {
            checkPDF(injectIntoLocalPDF, showLocalFileHelpPage);
          } else {
            fn(createError('local-file', 'Local non-PDF files are not supported'));
          }
        } else {
          checkPDF(injectIntoPDF, injectIntoHTML);
        }
      });
    };

    this.removeFromTab = function (tab, fn) {
      var url;
      fn = fn || function () {};

      if (isChromeURL(tab.url)) {
        return setTimeout(fn.bind(null, null));
      }

      if (isPDFViewerURL(tab.url)) {
        url = tab.url.slice(getPDFViewerURL('').length).split('#')[0];
        chromeTabs.update(tab.id, {
          url: decodeURIComponent(url)
        }, fn.bind(null, null));
      } else {
        chromeTabs.executeScript(tab.id, {
          code: [
            'var script = document.createElement("script");',
            'script.src = "' + extensionURL('/public/destroy.js') + '";',
            'document.body.appendChild(script);',
            'delete window.annotator;',
          ].join('\n')
        }, fn.bind(null, null));
      }
    };

    function getPDFViewerURL(url) {
      var PDF_VIEWER_URL = extensionURL('/content/web/viewer.html');
      return PDF_VIEWER_URL + '?file=' + encodeURIComponent(url);
    }

    function isPDFURL(url) {
      return url.toLowerCase().indexOf('.pdf') > 0;
    }

    function isPDFViewerURL(url) {
      return url.indexOf(getPDFViewerURL('')) === 0;
    }

    function isFileURL(url) {
      return url.indexOf("file://") === 0;
    }

    function isChromeURL(url) {
      return url.indexOf('chrome://') === 0 || url.indexOf('chrome-devtools://') === 0;
    }

    function injectionFailed(tab) {
      setBrowserAction(tab.id, state(tab.id, 'sleeping'));
    }

    function injectIntoPDF(tab, fn) {
      if (!isPDFViewerURL(tab.url)) {
        chromeTabs.update(tab.id, {
          url: getPDFViewerURL(tab.url)
        }, fn.bind(null, null));
      } else {
        setTimeout(fn);
      }
    }

    function injectIntoLocalPDF(tab, fn) {
      isAllowedFileSchemeAccess(function (isAllowed) {
        if (isAllowed) {
          injectIntoPDF(tab, fn);
        } else {
          setTimeout(fn.bind(null, createError('no-file-access', 'Local file scheme access denied')));
        }
      });
    }

    function injectIntoHTML(tab, fn) {
      chromeTabs.executeScript(tab.id, {
        file: 'public/embed.js'
      }, function (result) {
        if (result !== undefined) {
          chromeTabs.executeScript(tab.id, {
            code: 'window.annotator = true;'
          }, fn.bind(null, null));
        } else {
          setTimeout(fn.bind(null, createError('local-file', 'Local non-PDF files are not supported')));
        }
      });
    }

    function createError(type, description) {
      var err = new Error(description);
      err.type = type;
      return err;
    }

    // Render the help page. The helpSection should correspond to the id of a
    // section within the help page.
    function showHelpPage(helpSection, tab) {
      injectionFailed(tab);
      chromeTabs.update(tab.id, {
        url:  extensionURL('/help/permissions.html#' + helpSection)
      });
    }

    var showLocalFileHelpPage = showHelpPage.bind(null, 'local-file');
    var showNoFileAccessHelpPage = showHelpPage.bind(null, 'no-file-access');

    function injectConfig(tab, fn) {
      var src  = extensionURL('/public/config.js');
      var code = 'var script = document.createElement("script");' +
        'script.src = "{}";' +
        'document.body.appendChild(script);';

      chromeTabs.executeScript(tab.id, {code: code.replace('{}', src)}, fn);
    }
  };

  h.SidebarInjector = SidebarInjector;
})(window.h || (window.h = {}));
