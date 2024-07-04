import { render } from 'preact';

import CreateGroupForm from './components/CreateGroupForm';

function init() {
  const shadowHost = document.querySelector('#create-group-form')!;
  const shadowRoot = shadowHost.attachShadow({ mode: 'open' });
  render(<CreateGroupForm />, shadowRoot);
}

init();
