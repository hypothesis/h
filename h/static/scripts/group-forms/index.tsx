import { render } from 'preact';

import CreateEditGroupForm from './components/CreateEditGroupForm';
import { readConfig } from './config';

function init() {
  const shadowHost = document.querySelector('#create-group-form')!;
  const shadowRoot = shadowHost.attachShadow({ mode: 'open' });
  const config = readConfig();
  const stylesheetLinks = config.styles.map((stylesheetURL, index) => (
    <link
      key={`${stylesheetURL}${index}`}
      rel="stylesheet"
      href={stylesheetURL}
    />
  ));
  render(
    <>
      {stylesheetLinks}
      <CreateEditGroupForm />
    </>,
    shadowRoot,
  );
}

init();
