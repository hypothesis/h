import { render } from 'preact';

import { findContainer, readConfig } from '../forms-common/config';
import AppRoot from './components/AppRoot';
import type { ConfigObject } from './config';

function init() {
  const container = findContainer('#login-form');
  const config = readConfig<ConfigObject>();
  render(<AppRoot config={config} />, container);
}

init();
