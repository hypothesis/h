// Script injected into the page to trigger removal of any existing instances
// of the Hypothesis client.
(function () {
  'use strict';

  var annotatorLink =
    document.querySelector('link[type="application/annotator+html"]');

  if (annotatorLink) {
    // Dispatch a 'destroy' event which is handled by the code in
    // annotator/main.js to remove the client.
    var destroyEvent = new Event('destroy');
    annotatorLink.dispatchEvent(destroyEvent);
  }
}());
