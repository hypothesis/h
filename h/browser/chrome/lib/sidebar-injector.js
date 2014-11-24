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

    /* Injects the Hypothesis sidebar into the tab provided. The promise
     * will be rejected with an error if the injection fails. See errors.js
     * for the full list of errors.
     *
     * tab - A tab object representing the tab to insert the sidebar into.
     *
     * Returns a promise that will be resolved if the injection went well
     * otherwise it will be rejected with an error.
     */
    this.injectIntoTab = function (tab) {
      if (isFileURL(tab.url)) {
        return injectIntoLocalDocument(tab);
      } else {
        return injectIntoRemoteDocument(tab);
      }
    };

    /* Removes the Hypothesis sidebar from the tab provided. The callback
     * will be called when removal is complete. An error is passed as the
     * first argument to the callback if removal failed.
     *
     * tab - A tab object representing the tab to remove the sidebar from.
     *
     * Returns a promise that will be resolved if the removal succeeded
     * otherwise it will be rejected with an error.
     */
    this.removeFromTab = function (tab) {
      if (isPDFViewerURL(tab.url)) {
        return removeFromPDF(tab);
      } else {
        return removeFromHTML(tab);
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
      return url.indexOf("file:") === 0;
    }

    function isHTTPURL(url) {
      return url.indexOf('http:') === 0 || url.indexOf('https:') === 0;
    }

    function injectIntoLocalDocument(tab) {
      if (isPDFURL(tab.url)) {
        return injectIntoLocalPDF(tab);
      } else {
        return Promise.reject(new h.LocalFileError('Local non-PDF files are not supported'));
      }
    }

    function injectIntoRemoteDocument(tab) {
      return isPDFURL(tab.url) ? injectIntoPDF(tab) : injectIntoHTML(tab);
    }

    function injectIntoPDF(tab) {
      return new Promise(function (resolve, reject) {
        if (!isPDFViewerURL(tab.url)) {
          chromeTabs.update(tab.id, {url: getPDFViewerURL(tab.url)}, function () {
            resolve();
          });
        } else {
          resolve();
        }
      });
    }

    function injectIntoLocalPDF(tab) {
      return new Promise(function (resolve, reject) {
        isAllowedFileSchemeAccess(function (isAllowed) {
          if (isAllowed) {
            resolve(injectIntoPDF(tab));
          } else {
            reject(new h.NoFileAccessError('Local file scheme access denied'));
          }
        });
      });
    }

    function injectIntoHTML(tab) {
      return new Promise(function (resolve, reject) {
        if (!isHTTPURL(tab.url)) {
          return reject(new h.RestrictedProtocolError('Cannot load Hypothesis into chrome pages'));
        }

        return isSidebarInjected(tab.id).then(function (isInjected) {
          if (!isInjected) {
            injectConfig(tab.id).then(function () {
              chromeTabs.executeScript(tab.id, {
                code: 'window.annotator = true'
              }, function () {
                chromeTabs.executeScript(tab.id, {
                  file: 'public/embed.js'
                }, resolve);
              });
            });
          } else {
            resolve();
          }
        });
      });
    }

    function removeFromPDF(tab) {
      return new Promise(function (resolve) {
        var url = tab.url.slice(getPDFViewerURL('').length).split('#')[0];
        chromeTabs.update(tab.id, {
          url: decodeURIComponent(url)
        }, resolve);
      });
    }

    function removeFromHTML(tab) {
      return new Promise(function (resolve, reject) {
        if (!isHTTPURL(tab.url)) {
          return resolve();
        }

        return isSidebarInjected(tab.id).then(function (isInjected) {
          var src  = extensionURL('/public/destroy.js');
          var code = 'var script = document.createElement("script");' +
            'script.src = "{}";' +
            'document.body.appendChild(script);' +
            'delete window.annotator;';

          if (isInjected) {
            chromeTabs.executeScript(tab.id, {
              code: code.replace('{}', src)
            }, resolve);
          } else {
            resolve();
          }
        });
      });
    }

    function isSidebarInjected(tabId) {
      return new Promise(function (resolve, reject) {
        return chromeTabs.executeScript(tabId, {code: 'window.annotator'}, function (result) {
          resolve((result && result[0] === true) || false);
        });
      });
    }

    function injectConfig(tabId) {
      return new Promise(function (resolve) {
        var src  = extensionURL('/public/config.js');
        var code = 'var script = document.createElement("script");' +
          'script.src = "{}";' +
          'document.body.appendChild(script);';

        chromeTabs.executeScript(tabId, {code: code.replace('{}', src)}, resolve);
      });
    }
  }

  h.SidebarInjector = SidebarInjector;
})(window.h || (window.h = {}));
