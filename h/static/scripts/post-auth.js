'use strict';

/**
 * Script which runs in the small HTML page served by the OAuth Authorization
 * endpoint after successful authorization.
 *
 * It communicates the auth code back to the web app which initiated
 * authorization.
 */

const settings = require('./base/settings')(document);

function sendAuthResponse() {
  if (!window.opener) {
    console.error('The client window was closed');
    return;
  }

  const msg = {
    type: 'authorization_response',
    code: settings.code,
    state: settings.state,
  };

  // `document.documentMode` is a non-standard IE-only property.
  const isIE = 'documentMode' in document;
  if (isIE) {
    try {
      // IE 11 does not support `window.postMessage` between top-level windows
      // [1]. For the specific use case of the Hypothesis client, the sidebar
      // HTML page is on the same domain as the h service, so we can dispatch
      // the "message" event manually. Third-party clients will need to use
      // redirects to receive the auth code if they want to support IE 11.
      //
      // [1] https://blogs.msdn.microsoft.com/thebeebs/2011/12/21/postmessage-popups-and-ie/

      // Create an event in the target window.
      const clientWindow = window.opener;
      const event = clientWindow.document.createEvent('HTMLEvents');
      event.initEvent('message', true, true);

      // Clone the `msg` object into an object belonging to the target window.
      event.data = clientWindow.JSON.parse(JSON.stringify(msg));

      // Trigger "message" event listener in the target window.
      clientWindow.dispatchEvent(event);
      window.close();
    } catch (err) {
      console.error('The "web_message" response mode is not supported in IE', err);
    }
    return;
  }

  window.opener.postMessage(msg, settings.origin);
  window.close();
}

sendAuthResponse();

