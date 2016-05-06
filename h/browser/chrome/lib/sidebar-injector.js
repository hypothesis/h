'use strict';

var queryString = require('query-string');

var detectContentType = require('./detect-content-type');
var errors = require('./errors');
var util = require('./util');

var CONTENT_TYPE_HTML = 'HTML';
var CONTENT_TYPE_PDF = 'PDF';

function toIIFEString(fn) {
  return '(' + fn.toString() + ')()';
}

/**
 * Adds a <script> tag containing JSON config data to the page.
 *
 * Note that this function is stringified and injected into the page via a
 * content script, so it cannot reference any external variables.
 */
function addJSONScriptTagFn(name, content) {
  var scriptTag = document.createElement('script');
  scriptTag.className = name;
  scriptTag.textContent = content;
  scriptTag.type = 'application/json';
  document.head.appendChild(scriptTag);
}

/**
 * Extract the value returned by a content script injected via
 * chrome.tabs.executeScript() into the main frame of a page.
 *
 * executeScript() returns an array of results, one per frame which the script
 * was injected into.
 *
 * See https://developer.chrome.com/extensions/tabs#method-executeScript
 *
 * @param {Array<any>} result
 */
function extractContentScriptResult(result) {
  if (Array.isArray(result) && result.length > 0) {
    return result[0];
  } else if (typeof result === 'object') {
    // Firefox currently returns an object instead of
    // an array from executeScript()
    return result;
  } else {
    return;
  }
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

  var PDFViewerBaseURL = extensionURL('/content/web/viewer.html');

  if (typeof extensionURL !== 'function') {
    throw new TypeError('extensionURL must be a function');
  }

  if (typeof isAllowedFileSchemeAccess !== 'function') {
    throw new TypeError('isAllowedFileSchemeAccess must be a function');
  }

  /**
   * Injects the Hypothesis sidebar into the tab provided.
   *
   * @param {Tab} tab - A tab object representing the tab to insert the sidebar
   *        into.
   * @param {Object?} config - An object containing configuration info that
   *        is passed to the app when it loads.
   *
   * Returns a promise that will be resolved if the injection succeeded
   * otherwise it will be rejected with an error.
   */
  this.injectIntoTab = function(tab, config) {
    config = config || {};
    if (isFileURL(tab.url)) {
      return injectIntoLocalDocument(tab);
    } else {
      return injectIntoRemoteDocument(tab, config);
    }
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
    // Encode the original URL but preserve the fragment, so that a
    // '#annotations' fragment in the original URL will persist and trigger the
    // sidebar to focus and scroll to that annotation when the PDF viewer loads.
    var parsedURL = new URL(url);
    var hash = parsedURL.hash;
    parsedURL.hash = '';
    var encodedURL = encodeURIComponent(parsedURL.href);
    return PDFViewerBaseURL + '?file=' + encodedURL + hash;
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

  /**
   * Guess the content type of a page from the URL alone.
   *
   * This is a fallback for when it is not possible to inject
   * a content script to determine the type of content in the page.
   */
  function guessContentTypeFromURL(url) {
    if (url.indexOf('.pdf') !== -1) {
      return CONTENT_TYPE_PDF;
    } else {
      return CONTENT_TYPE_HTML;
    }
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
            var result = extractContentScriptResult(frameResults);
            if (result) {
              return result.type;
            } else {
              // If the content script threw an exception,
              // frameResults may be null or undefined.
              //
              // In that case, fall back to guessing based on the
              // tab URL
              return guessContentTypeFromURL(tab.url);
            }
          });
      } else {
        // We cannot inject a content script in order to determine the
        // file type, so fall back to a URL-based mechanism
        return Promise.resolve(guessContentTypeFromURL(tab.url));
      }
    });
  }

  /**
   * Returns true if a tab is displaying a PDF using the PDF.js-based
   * viewer bundled with the extension.
   */
  function isPDFViewerURL(url) {
    return url.indexOf(PDFViewerBaseURL) === 0;
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

  function injectIntoRemoteDocument(tab, config) {
    if (isPDFViewerURL(tab.url)) {
      return Promise.resolve();
    }

    if (!isSupportedURL(tab.url)) {
      // Chrome does not permit extensions to inject content scripts
      // into (chrome*):// URLs and other custom schemes.
      //
      // A common case where this happens is when the user has an
      // extension installed that provides a custom viewer for PDFs
      // (or some other format). In some cases we could extract the original
      // URL and open that in the Hypothesis viewer instead.
      var protocol = tab.url.split(':')[0];
      return Promise.reject(new errors.RestrictedProtocolError('Cannot load Hypothesis into ' + protocol + ' pages'));
    }

    return detectTabContentType(tab).then(function (type) {
      if (type === CONTENT_TYPE_PDF) {
        return injectIntoPDF(tab);
      } else {
        return injectConfig(tab.id, config).then(function () {
          return injectIntoHTML(tab);
        }).then(function (results) {
          var result = extractContentScriptResult(results);
          if (result &&
              typeof result.installedURL === 'string' &&
              result.installedURL.indexOf(extensionURL('/')) === -1) {
            throw new errors.AlreadyInjectedError(
              'Hypothesis is already injected into this page'
            );
          }
        });
      }
    });
  }

  function injectIntoPDF(tab) {
    if (isPDFViewerURL(tab.url)) {
      return Promise.resolve();
    }
    var updateFn = util.promisify(chromeTabs.update);
    return updateFn(tab.id, {url: getPDFViewerURL(tab.url)});
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
    return injectScript(tab.id, '/public/embed.js');
  }

  function removeFromPDF(tab) {
    return new Promise(function (resolve) {
      var parsedURL = new URL(tab.url);
      var originalURL = queryString.parse(parsedURL.search).file;
      if (!originalURL) {
        throw new Error('Failed to extract original URL from ' + tab.url);
      }
      var hash = parsedURL.hash;

      // If the original URL was a direct link, drop the #annotations fragment
      // as otherwise the Chrome extension will re-activate itself on this tab
      // when the original URL loads.
      if (hash.indexOf('#annotations:') === 0) {
        hash = '';
      }

      chromeTabs.update(tab.id, {
        url: decodeURIComponent(originalURL) + hash,
      }, resolve);
    });
  }

  function removeFromHTML(tab) {
    if (!isSupportedURL(tab.url)) {
      return Promise.resolve();
    }
    return injectScript(tab.id, '/public/destroy.js');
  }

  /**
   * Inject the script from the source file at `path` into the
   * page currently loaded in the tab at the given ID.
   */
  function injectScript(tabId, path) {
    return executeScriptFn(tabId, {file: path});
  }

  /**
   * Inject configuration information for the Hypothesis application
   * into the page as JSON data via a <meta> tag.
   *
   * A <meta> tag is used because that makes it available to JS content
   * running in isolated worlds.
   */
  function injectConfig(tabId, config) {
    var configStr = JSON.stringify(config).replace(/"/g, '\\"');
    var configCode =
      'var hypothesisConfig = "' + configStr + '";\n' +
      '(' + addJSONScriptTagFn.toString() + ')' +
      '("js-hypothesis-config", hypothesisConfig);\n';
    return executeScriptFn(tabId, {code: configCode});
  }
}

module.exports = SidebarInjector;
