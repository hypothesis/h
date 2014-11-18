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
        return setTimeout(fn.bind(null, new h.RestrictedProtocolError('Cannot load Hypothesis into chrome pages')));
      }

      function checkPDF(success, fallback) {
        if (isPDFURL(tab.url)) {
          success(tab, fn);
        } else {
          fallback(tab, fn);
        }
      }

      if (isFileURL(tab.url)) {
        checkPDF(injectIntoLocalPDF, function () {
          var err = new h.LocalFileError('Local non-PDF files are not supported');
          setTimeout(fn.bind(null, err));
        });
      } else {
        checkPDF(injectIntoPDF, injectIntoHTML);
      }
    };

    this.removeFromTab = function (tab, fn) {
      var url;
      fn = fn || function () {};

      if (isChromeURL(tab.url)) {
        return setTimeout(fn.bind(null, new h.RestrictedProtocolError('Cannot load Hypothesis into chrome pages')));
      }

      if (isPDFViewerURL(tab.url)) {
        url = tab.url.slice(getPDFViewerURL('').length).split('#')[0];
        chromeTabs.update(tab.id, {
          url: decodeURIComponent(url)
        }, fn.bind(null, null));
      } else {
        // TODO: Needs to check for local file permissions or just not run
        // when not injected.
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
      var isBrowser = url.indexOf('chrome:') === 0;
      var isDevtools = url.indexOf('chrome-devtools:') == 0;
      var isExtension = url.indexOf('chrome-extension:') === 0;
      return isBrowser || isDevtools || isExtension;
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
