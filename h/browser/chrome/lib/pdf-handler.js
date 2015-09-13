(function(h) {
  /* globals chrome */

  'use strict';

  // records PDF URLs as keys (value is `true`)
  var urls = {};
  var state;
  var VIEWER_URL = chrome.extension.getURL('content/web/viewer.html');

  /**
   * State machine for PDF Urls as well as utility functions for redirecting
   * to the PDF.js Viewer + Hypothesis
   * @constructor
   **/
  function PdfHandler(stateObj) {
    state = stateObj;
  };

  function getViewerURL(pdfUrl) {
    return VIEWER_URL + '?file=' + encodeURIComponent(pdfUrl);
  }

  /**
   * @param {Object} details First argument of the webRequest.onHeadersReceived
   *                         event. The property "url" is read.
   * @return {boolean} True if the PDF file should be downloaded.
   */
  function isPdfDownloadable(details) {
    if (details.url.indexOf('pdfjs.action=download') >= 0) {
      return true;
    }
    // Display the PDF viewer regardless of the Content-Disposition header
    // if the file is displayed in the main frame.
    if (details.type === 'main_frame') {
      return false;
    }
    var cdHeader = (details.responseHeaders &&
      getHeaderFromHeaders(details.responseHeaders, 'content-disposition'));
    return (cdHeader && /^attachment/i.test(cdHeader.value));
  }

  /**
   * Get the header from the list of headers for a given name.
   * @param {Array} headers responseHeaders of webRequest.onHeadersReceived
   * @return {undefined|{name: string, value: string}} The header, if found.
   */
  function getHeaderFromHeaders(headers, headerName) {
    for (var i = 0; i < headers.length; ++i) {
      var header = headers[i];
      if (header.name.toLowerCase() === headerName) {
        return header;
      }
    }
  }

  /**
   * Check if the request is a PDF file.
   * @param {Object} details First argument of the webRequest.onHeadersReceived
   *                         event. The properties "responseHeaders" and "url"
   *                         are read.
   * @return {boolean} True if the resource is a PDF file.
   */
  function isPdfFile(details) {
    var url = details.url;
    if (url in urls) {
      return true;
    } else {
      var header = getHeaderFromHeaders(details.responseHeaders,
          'content-type');
      if (header) {
        var headerValue = header.value.toLowerCase().split(';', 1)[0].trim();
        var isPdf = (headerValue === 'application/pdf' ||
                headerValue === 'application/octet-stream' &&
                details.url.toLowerCase().indexOf('.pdf') > 0);
        if (isPdf) {
          urls[url] = true;
        }
        return isPdf;
      }
    }
  }

  /**
   * Takes a set of headers, and set "Content-Disposition: attachment".
   * @param {Object} details First argument of the webRequest.onHeadersReceived
   *                         event. The property "responseHeaders" is read and
   *                         modified if needed.
   * @return {Object|undefined} The return value for the onHeadersReceived event.
   *                            Object with key "responseHeaders" if the headers
   *                            have been modified, undefined otherwise.
   */
  function getHeadersWithContentDispositionAttachment(details) {
    var headers = details.responseHeaders;
    var cdHeader = getHeaderFromHeaders(headers, 'content-disposition');
    if (!cdHeader) {
      cdHeader = {name: 'Content-Disposition'};
      headers.push(cdHeader);
    }
    if (!/^attachment/i.test(cdHeader.value)) {
      cdHeader.value = 'attachment' + cdHeader.value.replace(/^[^;]+/i, '');
      return {responseHeaders: headers};
    }
  }

  chrome.webRequest.onHeadersReceived.addListener(
    function(details) {
      // if we're not an active tab, do nothing
      if (!state.isTabActive(details.tabId)) {
        return;
      }

      if (details.method !== 'GET') {
        // Don't intercept POST requests until http://crbug.com/104058 is
        // fixed.
        return;
      }
      if (!isPdfFile(details)) {
        return;
      }
      if (isPdfDownloadable(details)) {
        // Force download by ensuring that Content-Disposition: attachment is
        // set
        return getHeadersWithContentDispositionAttachment(details);
      }

      var viewerUrl = getViewerURL(details.url);

      return {redirectUrl: viewerUrl};
    },
    {
      urls: [
        '<all_urls>'
      ],
      types: ['main_frame']
    },
    ['blocking', 'responseHeaders']);

  chrome.webRequest.onBeforeRequest.addListener(
    function onBeforeRequestForFTP(details) {
      // if we're not an active tab, do nothing
      if (!state.isTabActive(details.tabId)) {
        return;
      }

      if (isPdfDownloadable(details)) {
        return;
      }
      var viewerUrl = getViewerURL(details.url);
      return {redirectUrl: viewerUrl};
    },
    {
      urls: [
        'ftp://*/*.pdf',
        'ftp://*/*.PDF'
      ],
      types: ['main_frame']
    },
    ['blocking']);

  chrome.webRequest.onBeforeRequest.addListener(
    function(details) {
      // if we're not an active tab, do nothing
      if (!state.isTabActive(details.tabId)) {
        return;
      }

      if (isPdfDownloadable(details)) {
        return;
      }

      var viewerUrl = getViewerURL(details.url);

      return {redirectUrl: viewerUrl};
    },
    {
      urls: [
        'file://*/*.pdf',
        'file://*/*.PDF'
      ],
      types: ['main_frame']
    },
    ['blocking']);

  /**
   * Redirects the tab (specified with `tabId`) to `url`
   *
   * @returns Promise
   **/
  function updateTab(tabId, url) {
    return new Promise(function (resolve) {
      chrome.tabs.update(tabId, {url: url}, resolve);
    });
  }

  /**
   * Redirects tab to the PDF viewer
   * @param {Object} tab Chrome tabs.Tab object
   * @returns Promise
   **/
  PdfHandler.prototype.redirectToViewer = function(tab) {
    return updateTab(tab.id, getViewerURL(tab.url));
  };

  /**
   * Redirects tab to PDF (from viewer)
   * @param {Object} tab Chrome tabs.Tab object
   * @returns Promise
   **/
  PdfHandler.prototype.redirectToPdf = function(tab) {
    // TODO: could be smarter / safer
    // ...using code injection doesn't work because we'd need
    var pdf_url = decodeURIComponent(tab.url.split('?file=')[1]);
    return updateTab(tab.id, pdf_url);
  };

  /**
   * Check current browser session's list of known PDF URLs.
   * These are collected even if the annotate button is inactive--which allows
   * us to enable the PDF.js Viewer on an already loaded PDF.
   * @param {String} url
   * @return {Boolean}
   **/
  PdfHandler.prototype.isKnownPDF = function(url) {
    return (url in urls);
  };

  h.PdfHandler = PdfHandler;
})(window.h || (window.h = {}));
