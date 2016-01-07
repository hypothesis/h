/**
 * Returns the type of content in the current document,
 * currently either 'PDF' or 'HTML'.
 *
 * This function is injected as a content script into tabs in
 * order to detect the type of content on the page (PDF, HTML) etc.
 * by sniffing for viewer plugins.
 *
 * In future this could also be extended to support extraction of the URLs
 * of content in embedded viewers where that differs from the tab's
 * main URL.
 */
function detectContentType() {
  // check if this is the Chrome PDF viewer
  var chromePDFPluginSelector =
    'embed[type="application/pdf"][name="plugin"][id="plugin"]';
  if (document.querySelector(chromePDFPluginSelector)) {
    return {
      type: 'PDF',
    };
  } else {
    return {
      type: 'HTML',
    };
  }
}

module.exports = detectContentType;
