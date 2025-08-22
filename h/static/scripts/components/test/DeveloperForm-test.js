import { mount } from '@hypothesis/frontend-testing';

import { LoginFormsConfig } from '../../config';
import DeveloperForm from '../DeveloperForm';

describe('DeveloperForm', () => {
  function createComponent(configOverrides = {}) {
    const config = {
      csrfToken: 'test-csrf',
      token: null,
      ...configOverrides,
    };

    return mount(
      <LoginFormsConfig.Provider value={config}>
        <DeveloperForm />
      </LoginFormsConfig.Provider>,
    );
  }

  it('shows "Create API token" button when no token exists', () => {
    const wrapper = createComponent({ token: null });

    const formFooter = wrapper.find('FormFooter');
    assert.equal(formFooter.prop('submitLabel'), 'Create API token');
  });

  it('shows "Recreate API token" button when token exists', () => {
    const wrapper = createComponent({ token: 'existing-token' });

    const formFooter = wrapper.find('FormFooter');
    assert.equal(formFooter.prop('submitLabel'), 'Recreate API token');
  });

  it('does not show token input when no token exists', () => {
    const wrapper = createComponent({ token: null });

    assert.isFalse(wrapper.exists('Input[name="token"]'));
    assert.isFalse(wrapper.exists('CopyButton'));
  });

  it('shows token input and copy button when token exists', () => {
    const wrapper = createComponent({ token: 'my-secret-token' });

    const tokenInput = wrapper.find('Input[name="token"]');
    assert.isTrue(tokenInput.exists());
    assert.equal(tokenInput.prop('value'), 'my-secret-token');

    const copyButton = wrapper.find('CopyButton');
    assert.isTrue(copyButton.exists());
    assert.equal(copyButton.prop('value'), 'my-secret-token');
    assert.equal(copyButton.prop('title'), 'Copy token');
  });

  it('passes csrfToken to Form', () => {
    const wrapper = createComponent({ csrfToken: 'custom-csrf-token' });

    const form = wrapper.find('Form');
    assert.equal(form.prop('csrfToken'), 'custom-csrf-token');
  });
});
