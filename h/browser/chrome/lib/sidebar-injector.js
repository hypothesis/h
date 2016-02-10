'use strict';

var detectContentType = require('./detect-content-type');
var errors = require('./errors');
var settings = require('./settings');
var util = require('./util');

var CONTENT_TYPE_HTML = 'HTML';
var CONTENT_TYPE_PDF = 'PDF';

function toIIFEString(fn) {
  return '(' + fn.toString() + ')()';
}

function addMetaTagFn(name, content) {
  var metaTag = document.createElement('meta');
  metaTag.name = name;
  metaTag.content = content;
  document.head.appendChild(metaTag);
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
    if (isFileURL(tab.url)) {
      return injectIntoLocalDocument(tab);
    } else {
      return injectIntoRemoteDocument(tab);
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
            if (Array.isArray(frameResults)) {
              return frameResults[0].type;
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
        return injectIntoHTML(tab);
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
    return injectScript(tab.id, '/public/config.js').then(function () {
      return injectScript(tab.id, '/public/embed.js', {
        'hypothesis-resource-root': extensionURL('/').slice(0,-1),
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

  /**
   * Generates code to add a set of <meta> tags to
   * the page which expose keys and values from an @p env object.
   *
   * ie. Given '{ foo : "bar" }', this function will return
   * script code to add '<meta name="foo" content="bar">' to the
   * <head> element of the page.
   *
   * This enables configuration data to be shared amongst content
   * scripts which may be running in isolated worlds (see
   * https://developer.chrome.com/extensions/content_scripts)
   */
  function generateMetaTagCode(env) {
    var envSetupCode = '';
    if (env) {
      var addMetaTagFnStr = addMetaTagFn.toString();
      Object.keys(env).forEach(function (key) {
        var content = JSON.stringify(env[key].toString());
        envSetupCode += '(' + addMetaTagFnStr + ')' +
          '("' + key + '",' + content + ');';
      });
    }
    return envSetupCode;
  }

  /**
   * Inject the script from the source file at @p path into the
   * page currently loaded in the tab at the given ID.
   *
   * @param env An optional map of keys and values to expose to the
   *            injected script via the 'window.HYPOTHESIS_ENV' object.
   */
  function injectScript(tabId, path, env) {
    var src  = extensionURL(path);
    var code = generateMetaTagCode(env) +
      'var script = document.createElement("script");' +
      'script.src = "{}";' +
      'document.body.appendChild(script);';
    var code = code.replace('{}', src);
    return executeScriptFn(tabId, {code: code});
  }
}

module.exports = SidebarInjector;
