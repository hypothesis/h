(function(h) {

  /*
  Copyright 2012 Mozilla Foundation

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
  */

  /* globals chrome */

  'use strict';

  var state;

  var VIEWER_URL = chrome.extension.getURL('content/web/viewer.html');

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
    var header = getHeaderFromHeaders(details.responseHeaders, 'content-type');
    if (header) {
      var headerValue = header.value.toLowerCase().split(';', 1)[0].trim();
      return (headerValue === 'application/pdf' ||
              headerValue === 'application/octet-stream' &&
              details.url.toLowerCase().indexOf('.pdf') > 0);
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

  h.PdfHandler = function(stateObj) {
    state = stateObj;
  };
})(window.h || (window.h = {}));
