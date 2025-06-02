import { render } from 'preact';

import { readConfig } from '../forms-common/config';
import AppRoot from './components/AppRoot';
import type { ConfigObject } from './config';

function init() {
  const shadowHost = document.querySelector('#group-form')!;
  const shadowRoot = shadowHost.attachShadow({ mode: 'open' });
  const config = readConfig<ConfigObject>();
  render(<AppRoot config={config} />, shadowRoot);
}

init();
