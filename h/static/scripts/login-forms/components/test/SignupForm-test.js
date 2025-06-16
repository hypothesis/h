import { checkAccessibility, mount } from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';

import { Config } from '../../config';
import { $imports, default as SignupForm } from '../SignupForm';

describe('SignupForm', () => {
  let fakeConfig;

  beforeEach(() => {
    fakeConfig = {
      csrfToken: 'fake-csrf-token',
      formData: {
        username: '',
        email: '',
        password: '',
        privacy_accepted: false,
        comms_opt_in: false,
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
      emailField: wrapper.find('TextField[name="email"]'),
      passwordField: wrapper.find('TextField[name="password"]'),
      privacyCheckbox: wrapper.find('Checkbox[data-testid="privacy-accepted"]'),
      commsCheckbox: wrapper.find('Checkbox[data-testid="comms-opt-in"]'),
      submitButton: wrapper.find('Button[data-testid="submit-button"]'),
    };
  };

  const createWrapper = () => {
    const wrapper = mount(
      <Config.Provider value={fakeConfig}>
        <SignupForm />
      </Config.Provider>,
    );
    const elements = getElements(wrapper);
    return { wrapper, elements };
  };

  it('renders signup form', () => {
    const { elements } = createWrapper();
    const {
      csrfInput,
      usernameField,
      emailField,
      passwordField,
      privacyCheckbox,
      commsCheckbox,
    } = elements;

    assert.equal(csrfInput.prop('value'), fakeConfig.csrfToken);
    assert.equal(usernameField.prop('value'), '');
    assert.equal(emailField.prop('value'), '');
    assert.equal(passwordField.prop('value'), '');
    assert.isFalse(privacyCheckbox.prop('checked'));
    assert.isFalse(commsCheckbox.prop('checked'));
  });

  it('displays form errors', () => {
    fakeConfig.formErrors = {
      username: 'Invalid username',
      email: 'Invalid email',
      password: 'Invalid password',
      privacy_accepted: 'You must accept the privacy policy',
    };

    const { elements } = createWrapper();
    const { usernameField, emailField, passwordField, privacyCheckbox } =
      elements;

    assert.equal(
      usernameField.prop('fieldError'),
      fakeConfig.formErrors.username,
    );
    assert.equal(emailField.prop('fieldError'), fakeConfig.formErrors.email);
    assert.equal(
      passwordField.prop('fieldError'),
      fakeConfig.formErrors.password,
    );
    assert.equal(
      privacyCheckbox.prop('error'),
      fakeConfig.formErrors.privacy_accepted,
    );
  });

  it('pre-fills form fields from formData', () => {
    fakeConfig.formData = {
      username: 'testuser',
      email: 'test@example.com',
      password: 'testpassword',
      privacy_accepted: true,
      comms_opt_in: true,
    };

    const { elements } = createWrapper();
    const {
      usernameField,
      emailField,
      passwordField,
      privacyCheckbox,
      commsCheckbox,
    } = elements;

    assert.equal(usernameField.prop('value'), fakeConfig.formData.username);
    assert.equal(emailField.prop('value'), fakeConfig.formData.email);
    assert.equal(passwordField.prop('value'), fakeConfig.formData.password);
    assert.equal(
      privacyCheckbox.prop('checked'),
      fakeConfig.formData.privacy_accepted,
    );
    assert.equal(
      commsCheckbox.prop('checked'),
      fakeConfig.formData.comms_opt_in,
    );
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

  [
    {
      username: 'testuser',
      error: undefined,
    },
    {
      username: 'foo@bar',
      error: 'Must have only letters, numbers, periods and underscores.',
    },
  ].forEach(({ username, error }) => {
    it('shows error if username contains invalid characters', () => {
      const { wrapper, elements } = createWrapper();

      act(() => {
        elements.usernameField.prop('onChangeValue')(username);
      });
      wrapper.update();
      const updatedElements = getElements(wrapper);

      assert.equal(updatedElements.usernameField.prop('fieldError'), error);
    });
  });

  it('updates email when input changes', () => {
    const { wrapper, elements } = createWrapper();
    const email = 'test@example.com';

    act(() => {
      elements.emailField.prop('onChangeValue')(email);
    });
    wrapper.update();
    const updatedElements = getElements(wrapper);

    assert.equal(updatedElements.emailField.prop('value'), email);
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

  it('updates privacy checkbox when clicked', () => {
    const { wrapper, elements } = createWrapper();
    const input = elements.privacyCheckbox.find('input');
    act(() => {
      input.getDOMNode().checked = true;
      input.simulate('change');
    });
    wrapper.update();
    const updatedElements = getElements(wrapper);

    assert.isTrue(updatedElements.privacyCheckbox.prop('checked'));
  });

  it('updates communication opt-in checkbox when clicked', () => {
    const { wrapper, elements } = createWrapper();
    const input = elements.commsCheckbox.find('input');
    act(() => {
      input.getDOMNode().checked = true;
      input.simulate('change');
    });
    wrapper.update();
    const updatedElements = getElements(wrapper);

    assert.isTrue(updatedElements.commsCheckbox.prop('checked'));
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: () => createWrapper().wrapper }),
  );
});
