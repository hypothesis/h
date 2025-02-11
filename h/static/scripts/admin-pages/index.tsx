import { render } from 'preact';

import AdminGroupCreateEditForm from './components/AdminGroupCreateEditForm';
import { readConfig } from './config';

function init() {
  const shadowHost = document.querySelector('#admin-group-create-edit-form')!;
  const shadowRoot = shadowHost.attachShadow({ mode: 'open' });
  const config = readConfig();
  render(<AdminGroupCreateEditForm config={config} />, shadowRoot);
}

init();
