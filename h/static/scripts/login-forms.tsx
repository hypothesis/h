import { render } from 'preact';

import LoginAppRoot from './components/LoginAppRoot';
import type { LoginFormsConfigObject } from './config';
import { findContainer, readConfig } from './forms-common/config';

function init() {
  const container = findContainer('#login-form');
  const config = readConfig<LoginFormsConfigObject>();
  render(<LoginAppRoot config={config} />, container);
}

init();
