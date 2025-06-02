import { render } from 'preact';

import AppRoot from './components/AppRoot';
import { readConfig } from '../forms-common/config';
import type { ConfigObject } from './config';

function init() {
  const container = document.querySelector('#login-form')!;
  const config = readConfig<ConfigObject>();
  render(<AppRoot config={config} />, container);
}

init();
