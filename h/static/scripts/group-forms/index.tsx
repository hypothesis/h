import { render } from 'preact';

import AppRoot from './components/AppRoot';
import { readConfig } from './config';

function init() {
  const shadowHost = document.querySelector('#group-form')!;
  const shadowRoot = shadowHost.attachShadow({ mode: 'open' });
  const config = readConfig();
  render(<AppRoot config={config} />, shadowRoot);
}

init();
