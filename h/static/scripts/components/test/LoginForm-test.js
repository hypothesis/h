import { checkAccessibility, mount } from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';

import { LoginFormsConfig } from '../../config';
import { routes } from '../../routes';
import { $imports, default as LoginForm } from '../LoginForm';

describe('LoginForm', () => {
  let fakeConfig;

  beforeEach(() => {
    fakeConfig = {
      csrfToken: 'fake-csrf-token',
      form: {
        data: {
          username: '',
          password: '',
        },
        errors: {},
      },
      features: {
        log_in_with_orcid: true,
      },
      urls: {
        login: {
          facebook: '/oidc/login/facebook',
          google: '/oidc/login/google',
          orcid: '/oidc/login/orcid',
        },
      },
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
      cancelButton: wrapper.find('Button[data-testid="cancel-button"]'),
    };
  };

  const createWrapper = (props = {}) => {
    const wrapper = mount(
      <LoginFormsConfig.Provider value={fakeConfig}>
        <LoginForm {...props} />
      </LoginFormsConfig.Provider>,
    );
    const elements = getElements(wrapper);
    return { wrapper, elements };
  };

  it('renders the login form', () => {
    const { elements } = createWrapper();
    const {
      csrfInput,
      usernameField,
      passwordField,
      forgotPasswordLink,
      cancelButton,
    } = elements;

    assert.equal(csrfInput.prop('value'), fakeConfig.csrfToken);
    assert.equal(usernameField.prop('value'), '');
    assert.equal(passwordField.prop('value'), '');
    assert.equal(forgotPasswordLink.prop('href'), routes.forgotPassword);
    assert.isFalse(cancelButton.exists());
  });

  [
    { forOAuth: false, expected: 'Log in' },
    { forOAuth: true, expected: 'Log in to Hypothesis' },
  ].forEach(({ forOAuth, expected }) => {
    it('renders expected title', () => {
      fakeConfig.forOAuth = forOAuth;
      const { wrapper } = createWrapper();
      assert.equal(wrapper.find('h1').text().trim(), expected);
    });
  });

  it('displays form errors', () => {
    fakeConfig.form.errors = {
      username: 'Invalid username',
      password: 'Invalid password',
    };

    const { elements } = createWrapper();
    const { usernameField, passwordField } = elements;

    assert.equal(
      usernameField.prop('fieldError'),
      fakeConfig.form.errors.username,
    );
    assert.equal(
      passwordField.prop('fieldError'),
      fakeConfig.form.errors.password,
    );
  });

  it('pre-fills form fields from form data', () => {
    fakeConfig.form.data = {
      username: 'testuser',
      password: 'testpassword',
    };

    const { elements } = createWrapper();
    const { usernameField, passwordField } = elements;

    assert.equal(usernameField.prop('value'), fakeConfig.form.data.username);
    assert.equal(passwordField.prop('value'), fakeConfig.form.data.password);
  });

  [
    // Normal login page
    {
      prefillUsername: false,
      usernameError: false,
      autofocusUsername: true,
    },
    // Login page with prefilled username
    {
      prefillUsername: true,
      usernameError: false,
      autofocusUsername: false,
    },
    // Login page after login failure due to username issue
    {
      prefillUsername: true,
      usernameError: true,
      autofocusUsername: true,
    },
  ].forEach(({ prefillUsername, usernameError, autofocusUsername }) => {
    it('auto-focuses expected field', () => {
      fakeConfig.form.data = {
        username: prefillUsername ? 'johnsmith' : null,
      };
      if (usernameError) {
        fakeConfig.form.errors = {
          username: 'invalid username',
        };
      }

      const { elements } = createWrapper();
      const { usernameField, passwordField } = elements;

      assert.equal(usernameField.prop('autofocus'), autofocusUsername);
      assert.equal(passwordField.prop('autofocus'), !autofocusUsername);
    });
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

  it('hides social login options if `enableSocialLogin` is false', () => {
    fakeConfig.features = {
      log_in_with_google: true,
      log_in_with_orcid: true,
      log_in_with_facebook: true,
    };
    const { wrapper } = createWrapper();
    assert.isFalse(wrapper.exists('SocialLoginLink'));
  });

  ['google', 'facebook', 'orcid'].forEach(provider => {
    it('shows enabled social login options', () => {
      fakeConfig.urls.login = {
        [provider]: `https://example.com/oidc/login/${provider}`,
      };
      const { wrapper } = createWrapper({ enableSocialLogin: true });
      const login = wrapper.find('SocialLoginLink');
      assert.equal(login.prop('provider'), provider);
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: () => createWrapper().wrapper }),
  );
});
