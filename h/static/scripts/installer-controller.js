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

  // check for Chrome extension support. We also check here for !mobile
  // so that the page is correct when testing in Chrome dev tools with
  // mobile device simulation enabled
  var offerChromeInstall = uaDetect.chromeExtensionsSupported &&
                           !uaDetect.isMobile;
  var offerBookmarkletInstall = !offerChromeInstall &&
                                !uaDetect.isMobile &&
                                !uaDetect.isMicrosoftEdge;

  showIf('.js-install-chrome', offerChromeInstall);
  showIf('.js-install-bookmarklet', offerBookmarkletInstall);
  showIf('.js-install-any', offerChromeInstall || offerBookmarkletInstall);
}

function InstallerController(element) {
  showSupportedInstallers(element);

  // setup Via link form
  var proxyForm = document.querySelector('.js-proxy-form');
  proxyForm.addEventListener('submit', function (event) {
    event.preventDefault();
    var url = proxyForm.elements['url'].value;
    window.location.href = 'https://via.hypothes.is/' + url;
  });
}

module.exports = InstallerController;
