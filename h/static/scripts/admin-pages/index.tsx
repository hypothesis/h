import { render } from 'preact';

import AdminGroupCreateEditForm from './components/AdminGroupCreateEditForm';

function init() {
  render(<AdminGroupCreateEditForm />, document.querySelector('#admin-group-create-edit-form')!);
}

init();
