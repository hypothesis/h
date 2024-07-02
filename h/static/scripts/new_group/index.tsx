import { render } from 'preact';

import NewGroupApp from './components/NewGroupApp';

export function init() {
  const rootEl = document.querySelector('#app');

  render(<NewGroupApp />, rootEl);
}

init();
