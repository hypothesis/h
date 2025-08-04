import { checkAccessibility, mount } from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';

import { Config } from '../../config';
import { $imports, default as SignupForm } from '../SignupForm';

describe('SignupForm', () => {
  let fakeConfig;

  beforeEach(() => {
    fakeConfig = {
      csrfToken: 'fake-csrf-token',
      form: {
        data: {
          username: '',
          email: '',
          password: '',
          privacy_accepted: false,
          comms_opt_in: false,
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
    fakeConfig.form.errors = {
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
      fakeConfig.form.errors.username,
    );
    assert.equal(emailField.prop('fieldError'), fakeConfig.form.errors.email);
    assert.equal(
      passwordField.prop('fieldError'),
      fakeConfig.form.errors.password,
    );
    assert.equal(
      privacyCheckbox.prop('error'),
      fakeConfig.form.errors.privacy_accepted,
    );
  });

  it('pre-fills form fields from form data', () => {
    fakeConfig.form.data = {
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

    assert.equal(usernameField.prop('value'), fakeConfig.form.data.username);
    assert.equal(emailField.prop('value'), fakeConfig.form.data.email);
    assert.equal(passwordField.prop('value'), fakeConfig.form.data.password);
    assert.equal(
      privacyCheckbox.prop('checked'),
      fakeConfig.form.data.privacy_accepted,
    );
    assert.equal(
      commsCheckbox.prop('checked'),
      fakeConfig.form.data.comms_opt_in,
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
    {
      username: 'foo.',
      error: undefined,
    },
    {
      username: 'foo.',
      commit: true,
      error: 'May not start or end with a period.',
    },
  ].forEach(({ username, error, commit }) => {
    it('shows error if username contains invalid characters', () => {
      const { wrapper, elements } = createWrapper();

      act(() => {
        elements.usernameField.prop('onChangeValue')(username);
        if (commit) {
          elements.usernameField.prop('onCommitValue')(username);
        }
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

  it('disables submit button when form is submitted', () => {
    const { wrapper, elements } = createWrapper();
    const { form, submitButton } = elements;

    assert.isFalse(submitButton.getDOMNode().disabled);

    // Simulate submitting the form.
    //
    // To really submit the form we would have to populate all fields with
    // valid values and then use `HTMLFormElement.requestSubmit`.
    form.getDOMNode().dispatchEvent(new Event('submit'));
    wrapper.update();

    assert.isTrue(submitButton.getDOMNode().disabled);
  });

  context('when using social login', () => {
    function createSignupFormWithIdProvider({
      idProvider = 'orcid',
      idInfo = 'fake-jwt-token',
    } = {}) {
      fakeConfig.identity = {
        // This example matches the format of ORCID IDs, but the frontend
        // doesn't care about the format for any provider.
        provider_unique_id: '0000-0000-0000-0001',
      };

      const mockURL = new URL('http://example.com/signup');
      if (idInfo) {
        mockURL.searchParams.set('idinfo', idInfo);
      }
      const mockLocation = {
        href: mockURL.toString(),
      };

      const wrapper = mount(
        <Config.Provider value={fakeConfig}>
          <SignupForm idProvider={idProvider} location_={mockLocation} />
        </Config.Provider>,
      );

      return { wrapper };
    }

    it('displays connected identity', () => {
      const { wrapper } = createSignupFormWithIdProvider();

      const idBadge = wrapper.find('[data-testid="id-badge"]');
      assert.isTrue(idBadge.exists());
      assert.isTrue(idBadge.find('ORCIDIcon').exists());

      const connectedId = wrapper.find('[data-testid="connected-id"]');
      assert.equal(connectedId.text(), '0000-0000-0000-0001');
    });

    it('displays Google identity when using Google provider', () => {
      const { wrapper } = createSignupFormWithIdProvider({
        idProvider: 'google',
      });

      const idBadge = wrapper.find('[data-testid="id-badge"]');
      assert.isTrue(idBadge.exists());
      assert.isTrue(idBadge.find('GoogleIcon').exists());

      const connectedId = wrapper.find('[data-testid="connected-id"]');
      assert.equal(connectedId.text(), '0000-0000-0000-0001');
    });

    it('displays Facebook identity when using Facebook provider', () => {
      const { wrapper } = createSignupFormWithIdProvider({
        idProvider: 'facebook',
      });

      const idBadge = wrapper.find('[data-testid="id-badge"]');
      assert.isTrue(idBadge.exists());
      assert.isTrue(idBadge.find('FacebookIcon').exists());

      const connectedId = wrapper.find('[data-testid="connected-id"]');
      assert.equal(connectedId.text(), '0000-0000-0000-0001');
    });

    it('renders "idinfo" hidden input field', () => {
      const { wrapper } = createSignupFormWithIdProvider({
        idInfo: 'test-jwt-token',
      });
      const idInfoInput = wrapper.find('input[name="idinfo"]');
      assert.equal(idInfoInput.prop('value'), 'test-jwt-token');
    });

    it('does not display email field', () => {
      const { wrapper } = createSignupFormWithIdProvider();
      assert.isFalse(wrapper.exists('TextField[name="email"]'));
    });

    it('does not display password field', () => {
      const { wrapper } = createSignupFormWithIdProvider();
      assert.isFalse(wrapper.exists('TextField[name="password"]'));
    });

    it('displays an error if "idinfo" query param is missing', () => {
      const { wrapper } = createSignupFormWithIdProvider({ idInfo: null });

      const errorDiv = wrapper.find('[data-testid="error"]');

      assert.equal(
        errorDiv.text(),
        'Social login identity missing. Please try again.',
      );
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: () => createWrapper().wrapper }),
  );
});
