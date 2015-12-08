// Utility functions used on the page that presents the Hypothesis
// extension and bookmarklet installers

var uaDetect = require('./ua-detect');

function showSupportedInstallers(rootElement) {
  function showIf(selector, cond) {
    var elements = rootElement.querySelectorAll(selector);
    for (var i = 0; i < elements.length; i++) {
      if (cond) {
        elements[i].classList.remove('is-hidden');
      } else {
        elements[i].classList.add('is-hidden');
      }
    }
  }

  var canInstallChromeExt = uaDetect.isChrome && !uaDetect.isMobile;
  var canInstallBookmarklet = !uaDetect.isChrome && !uaDetect.isMobile &&
                              !uaDetect.isMicrosoftEdge;

  showIf('.js-install-chrome', canInstallChromeExt);
  showIf('.js-install-bookmarklet', canInstallBookmarklet);
  showIf('.js-install-any', canInstallChromeExt || canInstallBookmarklet);
}

module.exports = {
  showSupportedInstallers: showSupportedInstallers,
};
