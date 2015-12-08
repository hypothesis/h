module.exports = {
  isMobile: navigator.userAgent.match(/\b(Mobile)\b/),
  isMicrosoftEdge: navigator.userAgent.match(/\bEdge\b/),

  // we test for the existence of window.chrome here because Microsoft Edge
  // (and possibly others) serve
  isChrome: typeof window.chrome !== 'undefined' &&
            typeof window.chrome.webstore !== 'undefined',
};
