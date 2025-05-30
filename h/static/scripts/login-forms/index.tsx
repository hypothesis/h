import { render } from 'preact';

import AppRoot from './components/AppRoot';
import { readConfig } from './config';

function init() {
  const container = document.querySelector('#login-form')!;
  const config = readConfig();
  render(<AppRoot config={config} />, container);
}

init();
