(function (h) {
  'use strict';

  /* The SidebarInjector is used to deploy and remove the Hypothesis from
   * tabs. It also deals with loading PDF documents into the PDFjs viewer
   * when applicable.
   *
   * chromeTabs - An instance of chrome.tabs.
   * options    - An options oblect with additional helper methods.
   *   isAllowedFileSchemeAccess: A function that returns true if the user
   *   can access resources over the file:// protocol. See:
   *   https://developer.chrome.com/extensions/extension#method-isAllowedFileSchemeAccess
   *   extensionURL: A function that recieves a path and returns an absolute
   *   url. See: https://developer.chrome.com/extensions/extension#method-getURL
   */
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

    /* Injects the Hypothesis sidebar into the tab provided. The callback
     * will recieve an error if the injection fails. See errors.js
     * for the full list of errors.
     *
     * tab - A tab object representing the tab to insert the sidebar into.
     * fn  - A callback called when the insertion is complete.
     *
     * Returns nothing.
     */
    this.injectIntoTab = function (tab, fn) {
      fn = fn || function () {};

      if (isChromeURL(tab.url)) {
        return setTimeout(fn.bind(null, new h.RestrictedProtocolError('Cannot load Hypothesis into chrome pages')));
      }

      if (isFileURL(tab.url)) {
        injectIntoLocalDocument(tab, fn);
      } else {
        injectIntoRemoteDocument(tab, fn);
      }
    };

    /* Removes the Hypothesis sidebar from the tab provided. The callback
     * will be called when removal is complete. An error is passed as the
     * first argument to the callback if removal failed.
     *
     * tab - A tab object representing the tab to remove the sidebar from.
     * fn  - A callback called when the removal is complete.
     *
     * Returns nothing.
     */
    this.removeFromTab = function (tab, fn) {
      fn = fn || function () {};

      if (isChromeURL(tab.url)) {
        return setTimeout(fn.bind(null, new h.RestrictedProtocolError('Cannot load Hypothesis into chrome pages')));
      }

      if (isPDFViewerURL(tab.url)) {
        removeFromPDF(tab, fn);
      } else {
        removeFromHTML(tab, fn);
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
      var isBrowser = url.indexOf('chrome:') === 0;
      var isDevtools = url.indexOf('chrome-devtools:') == 0;
      var isExtension = url.indexOf('chrome-extension:') === 0;
      return isBrowser || isDevtools || isExtension;
    }

    function injectIntoLocalDocument(tab, fn) {
      var err;
      if (isPDFURL(tab.url)) {
        injectIntoLocalPDF(tab, fn);
      } else {
        err = new h.LocalFileError('Local non-PDF files are not supported');
        setTimeout(fn.bind(null, err));
      }
    }

    function injectIntoRemoteDocument(tab, fn) {
      if (isPDFURL(tab.url)) {
        injectIntoPDF(tab, fn);
      } else {
        injectIntoHTML(tab, fn);
      }
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
          setTimeout(fn.bind(null, new h.NoFileAccessError('Local file scheme access denied')));
        }
      });
    }

    function injectIntoHTML(tab, fn) {
      injectConfig(tab, function () {
        chromeTabs.executeScript(tab.id, {
          file: 'public/embed.js'
        }, function () {
          chromeTabs.executeScript(tab.id, {
            code: 'window.annotator = true;'
          }, fn.bind(null, null));
        });
      });
    }

    function removeFromPDF(tab, fn) {
      var url = tab.url.slice(getPDFViewerURL('').length).split('#')[0];
      chromeTabs.update(tab.id, {
        url: decodeURIComponent(url)
      }, fn.bind(null, null));
    }

    function removeFromHTML(tab, fn) {
      var src  = extensionURL('/public/destroy.js');
      var code = 'var script = document.createElement("script");' +
                 'script.src = "{}";' +
                 'document.body.appendChild(script);' +
                 'delete window.annotator;';

      // TODO: Needs to check for local file permissions or just not run
      // when not injected.
      chromeTabs.executeScript(tab.id, {
        code: code.replace('{}', src)
      }, fn.bind(null, null));
    }

    function injectConfig(tab, fn) {
      var src  = extensionURL('/public/config.js');
      var code = 'var script = document.createElement("script");' +
        'script.src = "{}";' +
        'document.body.appendChild(script);';

      chromeTabs.executeScript(tab.id, {
        code: code.replace('{}', src)
      }, fn.bind(null, null));
    }
  };

  h.SidebarInjector = SidebarInjector;
})(window.h || (window.h = {}));
