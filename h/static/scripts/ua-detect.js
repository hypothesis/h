module.exports = {
  isMobile: navigator.userAgent.match(/\b(Mobile)\b/),
  isMicrosoftEdge: navigator.userAgent.match(/\bEdge\b/),

  // we test for the existence of window.chrome.webstore
  //  here because Microsoft Edge (and possibly others) include
  // "Chrome" in their UA strings for website compatibility reasons
  // and Edge also provides an empty "window.chrome" object.
  chromeExtensionsSupported: typeof window.chrome !== 'undefined' &&
                             typeof window.chrome.webstore !== 'undefined',
};
