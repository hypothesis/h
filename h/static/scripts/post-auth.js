'use strict';

/**
 * Script which runs in the small HTML page served by the OAuth Authorization
 * endpoint after successful authorization.
 *
 * It communicates the auth code back to the web app which initiated
 * authorization.
 */

const settings = require('./base/settings')(document);

if (window.opener) {
  const msg = {
    type: 'authorization_response',
    code: settings.code,
    state: settings.state,
  };
  window.opener.postMessage(msg, settings.origin);
  window.close();
} else {
  console.error('The opening window has closed');
}

