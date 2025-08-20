import { render } from 'preact';

import GroupFormsAppRoot from './components/GroupFormsAppRoot';
import type { GroupFormsConfigObject } from './config';
import { findContainer, readConfig } from './util/config';

function init() {
  const container = findContainer('#group-form');
  const config = readConfig<GroupFormsConfigObject>();
  render(<GroupFormsAppRoot config={config} />, container);
}

init();
