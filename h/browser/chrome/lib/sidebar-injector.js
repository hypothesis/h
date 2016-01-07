'use strict';

var blocklist = require('../../../static/scripts/blocklist');
var detectContentType = require('./detect-content-type');
var errors = require('./errors');
var settings = require('./settings');
var util = require('./util');

var CONTENT_TYPE_HTML = 'HTML';
var CONTENT_TYPE_PDF = 'PDF';

function toIIFEString(fn) {
  return '(' + fn.toString() + ')()';
}

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

  var executeScriptFn = util.promisify(chromeTabs.executeScript);

  if (typeof extensionURL !== 'function') {
    throw new TypeError('extensionURL must be a function');
  }

  if (typeof isAllowedFileSchemeAccess !== 'function') {
    throw new TypeError('isAllowedFileSchemeAccess must be a function');
  }

  /* Injects the Hypothesis sidebar into the tab provided.
   *
   * tab - A tab object representing the tab to insert the sidebar into.
   *
   * Returns a promise that will be resolved if the injection succeeded
   * otherwise it will be rejected with an error.
   */
  this.injectIntoTab = function(tab) {
    return settings.then(function(settings) {
      if (blocklist.isBlocked(tab.url, settings.blocklist)) {
        return Promise.reject(new errors.BlockedSiteError(
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

  // returns true if the extension is permitted to inject
  // a content script into a tab with a given URL.
  function canInjectScript(url) {
    var canInject;
    if (isSupportedURL(url)) {
      canInject = Promise.resolve(true);
    } else if (isFileURL(url)) {
      canInject = util.promisify(isAllowedFileSchemeAccess)();
    } else {
      canInject = Promise.resolve(false);
    }
    return canInject;
  }

  function detectTabContentType(tab) {
    if (isPDFViewerURL(tab.url)) {
      return Promise.resolve(CONTENT_TYPE_PDF);
    }

    return canInjectScript(tab.url).then(function (canInject) {
      if (canInject) {
        return executeScriptFn(tab.id, {
            code: toIIFEString(detectContentType)
          }).then(function (frameResults) {
            return frameResults[0].type;
          });
      } else {
        // we cannot inject a content script in order to determine the
        // file type, so fall back to a URL-based mechanism
        if (tab.url.indexOf('.pdf') !== -1) {
          return Promise.resolve(CONTENT_TYPE_PDF);
        } else {
          return Promise.resolve(CONTENT_TYPE_HTML);
        }
      }
    });
  }

  function isPDFViewerURL(url) {
    return url.indexOf(getPDFViewerURL('')) === 0;
  }

  function isFileURL(url) {
    return url.indexOf("file:") === 0;
  }

  function isSupportedURL(url) {
    // Injection of content scripts is limited to a small number of protocols,
    // see https://developer.chrome.com/extensions/match_patterns
    var parsedURL = new URL(url);
    var SUPPORTED_PROTOCOLS = ['http:', 'https:', 'ftp:'];
    return SUPPORTED_PROTOCOLS.some(function (protocol) {
      return parsedURL.protocol === protocol;
    });
  }

  function injectIntoLocalDocument(tab) {
    return detectTabContentType(tab).then(function (type) {
      if (type === CONTENT_TYPE_PDF) {
        return injectIntoLocalPDF(tab);
      } else {
        return Promise.reject(new errors.LocalFileError('Local non-PDF files are not supported'));
      }
    });
  }

  function injectIntoRemoteDocument(tab) {
    return detectTabContentType(tab).then(function (type) {
      if (type === CONTENT_TYPE_PDF) {
        return injectIntoPDF(tab);
      } else {
        return injectIntoHTML(tab);
      }
    });
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
          reject(new errors.NoFileAccessError('Local file scheme access denied'));
        }
      });
    });
  }

  function injectIntoHTML(tab) {
    return new Promise(function (resolve, reject) {
      if (!isSupportedURL(tab.url)) {
        var protocol = tab.url.split(':')[0];
        return reject(new errors.RestrictedProtocolError('Cannot load Hypothesis into ' + protocol + ' pages'));
      }

      return injectScript(tab.id, '/public/config.js').then(function () {
        injectScript(tab.id, '/public/embed.js').then(resolve);
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

module.exports = SidebarInjector;
