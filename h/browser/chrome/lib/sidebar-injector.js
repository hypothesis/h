(function (h) {
  'use strict';

  /* The SidebarInjector is used to deploy and remove the Hypothesis sidebar
   * from tabs. It also deals with loading PDF documents into the PDF.js viewer
   * when applicable.
   *
   * chromeTabs - An instance of chrome.tabs.
   * dependencies - An object with additional helper methods.
   *   isAllowedFileSchemeAccess: A function that returns true if the user
   *   can access resources over the file:// protocol. See:
   *   https://developer.chrome.com/extensions/extension#method-isAllowedFileSchemeAccess
   *   extensionURL: A function that receives a path and returns an absolute
   *   url. See: https://developer.chrome.com/extensions/extension#method-getURL
   */
  function SidebarInjector(chromeTabs, dependencies) {
    dependencies = dependencies || {};

    var isAllowedFileSchemeAccess = dependencies.isAllowedFileSchemeAccess;
    var extensionURL = dependencies.extensionURL;

    if (typeof extensionURL !== 'function') {
      throw new TypeError('extensionURL must be a function');
    }

    if (typeof isAllowedFileSchemeAccess !== 'function') {
      throw new TypeError('isAllowedFileSchemeAccess must be a function');
    }

    /* Return a Promise whose value is the blocklist from the blocklist.json
     * file that's packaged with the Chrome extension, as an object.
     */
    function loadBlocklist() {
      return new Promise(function(resolve, reject) {
        var request = new XMLHttpRequest();
        request.onload = function() {
          resolve(JSON.parse(this.responseText));
        };
        request.open('GET', '/blocklist.json');
        request.send(null);
      });
    }

    /* Injects the Hypothesis sidebar into the tab provided.
     *
     * tab - A tab object representing the tab to insert the sidebar into.
     *
     * Returns a promise that will be resolved if the injection succeeded
     * otherwise it will be rejected with an error.
     */
    this.injectIntoTab = function (tab) {
      return loadBlocklist().then(function(blocklist) {
        if (h.blocklist.isBlocked(tab.url, blocklist)) {
          return Promise.reject(
            new h.BlockedSiteError(
              "Hypothesis doesn't work on this site yet."));
        }

        if (isFileURL(tab.url)) {
          return injectIntoLocalDocument(tab);
        } else if (!isPDFViewerURL(tab.url)) {
          return injectIntoHTML(tab);
        }
      });
    };

    /* Removes the Hypothesis sidebar from the tab provided.
     *
     * tab - A tab object representing the tab to remove the sidebar from.
     *
     * Returns a promise that will be resolved if the removal succeeded
     * otherwise it will be rejected with an error.
     */
    this.removeFromTab = function (tab) {
      return removeFromHTML(tab);
    };

    function getPDFViewerURL(url) {
      var PDF_VIEWER_URL = extensionURL('/content/web/viewer.html');
      return PDF_VIEWER_URL + '?file=' + encodeURIComponent(url);
    }

    function isPDFViewerURL(url) {
      return url.indexOf(getPDFViewerURL('')) === 0;
    }

    function isFileURL(url) {
      return url.indexOf("file:") === 0;
    }

    function isSupportedURL(url) {
      var SUPPORTED_PROTOCOLS = ['http:', 'https:', 'ftp:'];
      return SUPPORTED_PROTOCOLS.some(function (protocol) {
        return url.indexOf(protocol) === 0;
      });
    }

    function injectIntoLocalDocument(tab) {
      return Promise.reject(new h.LocalFileError('Local non-PDF files are not supported'));
    }

    function injectIntoHTML(tab) {
      return new Promise(function (resolve, reject) {
        if (!isSupportedURL(tab.url)) {
          var protocol = tab.url.split(':')[0];
          return reject(new h.RestrictedProtocolError('Cannot load Hypothesis into ' + protocol + ' pages'));
        }

        return injectScript(tab.id, '/public/config.js').then(function () {
          injectScript(tab.id, '/public/embed.js').then(resolve);
        });
      });
    }

    function removeFromHTML(tab) {
      return new Promise(function (resolve, reject) {
        if (!isSupportedURL(tab.url)) {
          return resolve();
        }
        injectScript(tab.id, '/public/destroy.js').then(resolve);
      });
    }

    function injectScript(tabId, path) {
      return new Promise(function (resolve) {
        var src  = extensionURL(path);
        var code = 'var script = document.createElement("script");' +
          'script.src = "{}";' +
          'document.body.appendChild(script);';
        var code = code.replace('{}', src);

        chromeTabs.executeScript(tabId, {code: code}, resolve);
      });
    }
  }

  h.SidebarInjector = SidebarInjector;
})(window.h || (window.h = {}));
