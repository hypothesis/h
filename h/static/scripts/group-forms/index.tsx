import { render } from 'preact';

import CreateGroupForm from './components/CreateGroupForm';

function init() {
  render(<CreateGroupForm />, document.querySelector('#create-group-form'));
}

init();
