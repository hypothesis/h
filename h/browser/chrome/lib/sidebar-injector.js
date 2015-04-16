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
        } else {
          return injectIntoRemoteDocument(tab);
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

    function isSupportedURL(url) {
      var SUPPORTED_PROTOCOLS = ['http:', 'https:', 'ftp:'];
      return SUPPORTED_PROTOCOLS.some(function (protocol) {
        return url.indexOf(protocol) === 0;
      });
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
        if (!isSupportedURL(tab.url)) {
          var protocol = tab.url.split(':')[0];
          return reject(new h.RestrictedProtocolError('Cannot load Hypothesis into ' + protocol + ' pages'));
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
        if (!isSupportedURL(tab.url)) {
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
          var isAnnotatorSet = !!(result && result[0]);
          resolve(isAnnotatorSet);
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
