import { checkAccessibility, mount } from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';

import { Config } from '../../config';
import { routes } from '../../routes';
import { $imports, default as LoginForm } from '../LoginForm';

describe('LoginForm', () => {
  let fakeConfig;

  beforeEach(() => {
    fakeConfig = {
      csrfToken: 'fake-csrf-token',
      formData: {
        username: '',
        password: '',
      },
      formErrors: {},
    };
  });

  afterEach(() => {
    $imports.$restore();
  });

  const getElements = wrapper => {
    return {
      form: wrapper.find('form[data-testid="form"]'),
      csrfInput: wrapper.find('input[name="csrf_token"]'),
      usernameField: wrapper.find('TextField[name="username"]'),
      passwordField: wrapper.find('TextField[name="password"]'),
      forgotPasswordLink: wrapper.find('a[data-testid="forgot-password-link"]'),
    };
  };

  const createWrapper = () => {
    const wrapper = mount(
      <Config.Provider value={fakeConfig}>
        <LoginForm />
      </Config.Provider>,
    );
    const elements = getElements(wrapper);
    return { wrapper, elements };
  };

  it('renders the login form', () => {
    const { elements } = createWrapper();
    const {
      form,
      csrfInput,
      usernameField,
      passwordField,
      forgotPasswordLink,
    } = elements;

    assert.equal(form.prop('action'), routes.login);
    assert.equal(csrfInput.prop('value'), fakeConfig.csrfToken);
    assert.equal(usernameField.prop('value'), '');
    assert.equal(passwordField.prop('value'), '');
    assert.equal(forgotPasswordLink.prop('href'), routes.forgotPassword);
  });

  it('displays form errors', () => {
    fakeConfig.formErrors = {
      username: 'Invalid username',
      password: 'Invalid password',
    };

    const { elements } = createWrapper();
    const { usernameField, passwordField } = elements;

    assert.equal(
      usernameField.prop('fieldError'),
      fakeConfig.formErrors.username,
    );
    assert.equal(
      passwordField.prop('fieldError'),
      fakeConfig.formErrors.password,
    );
  });

  it('pre-fills form fields from formData', () => {
    fakeConfig.formData = {
      username: 'testuser',
      password: 'testpassword',
    };

    const { elements } = createWrapper();
    const { usernameField, passwordField } = elements;

    assert.equal(usernameField.prop('value'), fakeConfig.formData.username);
    assert.equal(passwordField.prop('value'), fakeConfig.formData.password);
  });

  it('updates username when input changes', () => {
    const { wrapper, elements } = createWrapper();
    const username = 'testuser';

    act(() => {
      elements.usernameField.prop('onChangeValue')(username);
    });
    wrapper.update();
    const updatedElements = getElements(wrapper);

    assert.equal(updatedElements.usernameField.prop('value'), username);
  });

  it('updates password when input changes', () => {
    const { wrapper, elements } = createWrapper();
    const password = 'newpassword';

    act(() => {
      elements.passwordField.prop('onChangeValue')(password);
    });
    wrapper.update();
    const updatedElements = getElements(wrapper);

    assert.equal(updatedElements.passwordField.prop('value'), password);
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: () => createWrapper().wrapper }),
  );
});
