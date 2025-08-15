import { render } from 'preact';

import GroupFormsAppRoot from './components/GroupFormsAppRoot';
import type { GroupFormsConfigObject } from './config';
import { findContainer, readConfig } from './forms-common/config';

function init() {
  const container = findContainer('#group-form');
  const config = readConfig<GroupFormsConfigObject>();
  render(<GroupFormsAppRoot config={config} />, container);
}

init();
