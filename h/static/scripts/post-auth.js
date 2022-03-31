/**
 * Script which runs in the small HTML page served by the OAuth Authorization
 * endpoint after successful authorization.
 *
 * It communicates the auth code back to the web app which initiated
 * authorization.
 */

import { settings } from './base/settings';

const appSettings = settings(document);

function sendAuthResponse() {
  if (!window.opener) {
    console.error('The client window was closed');
    return;
  }

  const msg = {
    type: 'authorization_response',
    code: appSettings.code,
    state: appSettings.state,
  };

  window.opener.postMessage(msg, appSettings.origin);
  window.close();
}

sendAuthResponse();
