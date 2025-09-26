import { checkAccessibility, mount } from '@hypothesis/frontend-testing';

import { LoginFormsConfig } from '../../config';
import {
  $imports,
  default as AccountSettingsForms,
} from '../AccountSettingsForms.tsx';

describe('AccountSettingsForms', () => {
  let fakeConfig;
  let fakeCallAPI;

  beforeEach(() => {
    fakeConfig = {
      csrfToken: 'fakeCsrfToken',
      features: {
        log_in_with_google: true,
        log_in_with_facebook: true,
        log_in_with_orcid: true,
      },
      forms: {
        email: {
          data: {},
        },
        password: {
          data: {},
        },
      },
      context: {
        user: {
          has_password: true,
          preferences: {
            show_orcid_id_on_profile: true,
          },
        },
        identities: {
          google: { connected: false },
          facebook: { connected: false },
          orcid: { connected: false },
        },
      },
      routes: {
        'oidc.connect.google': 'https://example.com/oidc/connect/google',
        'oidc.connect.facebook': 'https://example.com/oidc/connect/facebook',
        'oidc.connect.orcid': 'https://example.com/oidc/connect/orcid',
        identity_delete: 'https://example.com/account/settings/identity',
      },
      api: {
        updateUserPrefs: {
          method: 'PATCH',
          url: 'https://example.com/api/profile',
          headers: { foo: 'bar' },
        },
      },
    };

    fakeCallAPI = sinon.stub();

    $imports.$mock({
      '../util/api': {
        callAPI: fakeCallAPI,
      },
    });
  });

  const getElements = wrapper => {
    const emailFormSelector = '[data-testid="email-form"]';
    const passwordFormSelector = '[data-testid="password-form"]';

    return {
      emailForm: {
        form: wrapper.find(emailFormSelector),
        csrfInput: wrapper.find(
          `${emailFormSelector} input[name="csrf_token"]`,
        ),
        formIdInput: wrapper.find(
          `${emailFormSelector} input[name="__formid__"]`,
        ),
        currentEmail: wrapper.find(
          `${emailFormSelector} [data-testid="current-email"]`,
        ),
        emailField: wrapper.find(
          `${emailFormSelector} TextField[name="email"]`,
        ),
        passwordField: wrapper.find(
          `${emailFormSelector} TextField[name="password"]`,
        ),
        submitButton: wrapper.find(
          `${emailFormSelector} [data-testid="submit-button"]`,
        ),
      },
      passwordForm: {
        form: wrapper.find(passwordFormSelector),
        csrfInput: wrapper.find(
          `${passwordFormSelector} input[name="csrf_token"]`,
        ),
        formIdInput: wrapper.find(
          `${passwordFormSelector} input[name="__formid__"]`,
        ),
        currentPasswordField: wrapper.find(
          `${passwordFormSelector} TextField[name="password"]`,
        ),
        newPasswordField: wrapper.find(
          `${passwordFormSelector} TextField[name="new_password"]`,
        ),
        confirmNewPasswordField: wrapper.find(
          `${passwordFormSelector} TextField[name="new_password_confirm"]`,
        ),
        submitButton: wrapper.find(
          `${passwordFormSelector} [data-testid="submit-button"]`,
        ),
      },
      connectAccountEl: wrapper.find('[data-testid="connect-your-account"]'),
      connectAccountLinks: {
        google: wrapper.find('[data-testid="connect-account-link-google"]'),
        facebook: wrapper.find('[data-testid="connect-account-link-facebook"]'),
        orcid: wrapper.find('[data-testid="connect-account-link-orcid"]'),
      },
      removeAccountForms: {
        google: {
          form: wrapper.find('[data-testid="remove-account-form-google"] form'),
          csrfInput: wrapper.find(
            '[data-testid="remove-account-form-google"] input[name="csrf_token"]',
          ),
          providerInput: wrapper.find(
            '[data-testid="remove-account-form-google"] input[name="provider"]',
          ),
          providerUniqueIdInput: wrapper.find(
            '[data-testid="remove-account-form-google"] input[name="provider_unique_id"]',
          ),
          submitButton: wrapper.find(
            '[data-testid="remove-account-form-google"] Button[type="submit"]',
          ),
        },
        facebook: {
          form: wrapper.find(
            '[data-testid="remove-account-form-facebook"] form',
          ),
          csrfInput: wrapper.find(
            '[data-testid="remove-account-form-facebook"] input[name="csrf_token"]',
          ),
          providerInput: wrapper.find(
            '[data-testid="remove-account-form-facebook"] input[name="provider"]',
          ),
          providerUniqueIdInput: wrapper.find(
            '[data-testid="remove-account-form-facebook"] input[name="provider_unique_id"]',
          ),
          submitButton: wrapper.find(
            '[data-testid="remove-account-form-facebook"] Button[type="submit"]',
          ),
        },
        orcid: {
          form: wrapper.find('[data-testid="remove-account-form-orcid"] form'),
          csrfInput: wrapper.find(
            '[data-testid="remove-account-form-orcid"] input[name="csrf_token"]',
          ),
          providerInput: wrapper.find(
            '[data-testid="remove-account-form-orcid"] input[name="provider"]',
          ),
          providerUniqueIdInput: wrapper.find(
            '[data-testid="remove-account-form-orcid"] input[name="provider_unique_id"]',
          ),
          submitButton: wrapper.find(
            '[data-testid="remove-account-form-orcid"] Button[type="submit"]',
          ),
        },
      },
      showOrcidIdCheckbox: wrapper.find(
        'Checkbox[data-testid="show-orcid-id-checkbox"]',
      ),
    };
  };

  const createWrapper = () => {
    const wrapper = mount(
      <LoginFormsConfig.Provider value={fakeConfig}>
        <AccountSettingsForms />
      </LoginFormsConfig.Provider>,
    );
    const elements = getElements(wrapper);
    return { wrapper, elements };
  };

  it('includes the CSRF token in the forms', () => {
    const { elements } = createWrapper();

    assert.equal(elements.emailForm.csrfInput.prop('value'), 'fakeCsrfToken');
    assert.equal(
      elements.passwordForm.csrfInput.prop('value'),
      'fakeCsrfToken',
    );
  });

  it('includes the right __formid__ elements in the forms', () => {
    const { elements } = createWrapper();

    assert.equal(elements.emailForm.formIdInput.prop('value'), 'email');
    assert.equal(elements.passwordForm.formIdInput.prop('value'), 'password');
  });

  it('renders the forms with empty fields', () => {
    const { elements } = createWrapper();

    assert.equal(elements.emailForm.emailField.prop('value'), '');
    assert.isFalse(elements.emailForm.currentEmail.exists());
    assert.equal(elements.emailForm.emailField.prop('fieldError'), undefined);
    assert.equal(elements.emailForm.passwordField.prop('value'), '');
    assert.equal(
      elements.emailForm.passwordField.prop('fieldError'),
      undefined,
    );
    assert.equal(elements.passwordForm.currentPasswordField.prop('value'), '');
    assert.equal(
      elements.passwordForm.currentPasswordField.prop('fieldError'),
      undefined,
    );
    assert.equal(elements.passwordForm.newPasswordField.prop('value'), '');
    assert.equal(
      elements.passwordForm.newPasswordField.prop('fieldError'),
      undefined,
    );
    assert.equal(
      elements.passwordForm.confirmNewPasswordField.prop('value'),
      '',
    );
    assert.equal(
      elements.passwordForm.confirmNewPasswordField.prop('fieldError'),
      undefined,
    );
  });

  it('pre-fills the forms fields with data from js-config', () => {
    fakeConfig.forms.email.data = {
      email: 'email.prefilled.email',
      password: 'email.prefilled.password',
    };
    fakeConfig.forms.password.data = {
      password: 'password.prefilled.password',
      new_password: 'password.prefilled.new_password',
      new_password_confirm: 'password.prefilled.new_password_confirm',
    };

    const { elements } = createWrapper();

    assert.equal(
      elements.emailForm.emailField.prop('value'),
      fakeConfig.forms.email.data.email,
    );
    assert.equal(
      elements.emailForm.passwordField.prop('value'),
      fakeConfig.forms.email.data.password,
    );
    assert.equal(
      elements.passwordForm.currentPasswordField.prop('value'),
      fakeConfig.forms.password.data.password,
    );
    assert.equal(
      elements.passwordForm.newPasswordField.prop('value'),
      fakeConfig.forms.password.data.new_password,
    );
    assert.equal(
      elements.passwordForm.confirmNewPasswordField.prop('value'),
      fakeConfig.forms.password.data.new_password_confirm,
    );
  });

  it('shows the current email address', () => {
    fakeConfig.context.user.email = 'current_email';

    const { elements } = createWrapper();

    assert.equal(elements.emailForm.currentEmail.text(), 'current_email');
  });

  it('omits confirm password fields if the user has no password', () => {
    fakeConfig.context.user.has_password = false;

    const { elements } = createWrapper();

    assert.isFalse(elements.emailForm.passwordField.exists());
    assert.isFalse(elements.passwordForm.currentPasswordField.exists());
  });

  it('renders per-field error messages from js-config', () => {
    fakeConfig.forms.email.errors = {
      email: 'email.error.email',
      password: 'email.error.password',
    };
    fakeConfig.forms.password.errors = {
      password: 'password.error.password',
      new_password: 'password.error.new_password',
      new_password_confirm: 'password.error.new_password_confirm',
    };

    const { elements } = createWrapper();

    assert.equal(
      elements.emailForm.emailField.prop('fieldError'),
      fakeConfig.forms.email.errors.email,
    );
    assert.equal(
      elements.emailForm.passwordField.prop('fieldError'),
      fakeConfig.forms.email.errors.password,
    );
    assert.equal(
      elements.passwordForm.currentPasswordField.prop('fieldError'),
      fakeConfig.forms.password.errors.password,
    );
    assert.equal(
      elements.passwordForm.newPasswordField.prop('fieldError'),
      fakeConfig.forms.password.errors.new_password,
    );
    assert.equal(
      elements.passwordForm.confirmNewPasswordField.prop('fieldError'),
      fakeConfig.forms.password.errors.new_password_confirm,
    );
  });

  it('includes the social connect links', () => {
    const { elements } = createWrapper();

    assert.equal(
      elements.connectAccountLinks.google.prop('href'),
      fakeConfig.routes['oidc.connect.google'],
    );
    assert.equal(
      elements.connectAccountLinks.facebook.prop('href'),
      fakeConfig.routes['oidc.connect.facebook'],
    );
    assert.equal(
      elements.connectAccountLinks.orcid.prop('href'),
      fakeConfig.routes['oidc.connect.orcid'],
    );
  });

  it('indicates when social accounts are already connected', () => {
    fakeConfig.context.identities.google.connected = true;
    fakeConfig.context.identities.google.provider_unique_id =
      'google_provider_unique_id';
    fakeConfig.context.identities.facebook.connected = true;
    fakeConfig.context.identities.orcid.connected = true;
    fakeConfig.context.identities.orcid.url =
      'https://orcid.org/0000-0002-6373-1308';

    const { elements } = createWrapper();

    assert.equal(elements.connectAccountLinks.google.prop('href'), undefined);
    assert.equal(elements.connectAccountLinks.facebook.prop('href'), undefined);
    assert.equal(
      elements.connectAccountLinks.orcid.prop('href'),
      'https://orcid.org/0000-0002-6373-1308',
    );

    ['google', 'facebook', 'orcid'].forEach(provider => {
      assert.equal(
        elements.removeAccountForms[provider].form.prop('action'),
        fakeConfig.routes.identity_delete,
      );
      assert.equal(
        elements.removeAccountForms[provider].csrfInput.prop('value'),
        fakeConfig.csrfToken,
      );
      assert.equal(
        elements.removeAccountForms[provider].providerInput.prop('value'),
        provider,
      );
      assert.equal(
        elements.removeAccountForms[provider].providerUniqueIdInput.prop(
          'value',
        ),
        fakeConfig.context.identities[provider].provider_unique_id,
      );
      assert.equal(
        elements.removeAccountForms[provider].submitButton.text(),
        'Remove',
      );
    });
  });

  it('omits the social account links when the features are disabled', () => {
    fakeConfig.features.log_in_with_google = false;
    fakeConfig.features.log_in_with_facebook = false;
    fakeConfig.features.log_in_with_orcid = false;

    const { elements } = createWrapper();

    assert.isFalse(elements.connectAccountEl.exists());
    assert.isFalse(elements.connectAccountLinks.google.exists());
    assert.isFalse(elements.connectAccountLinks.facebook.exists());
    assert.isFalse(elements.connectAccountLinks.orcid.exists());
  });

  it('doesn\t render the show-orcid-id checkbox if no orcid id is connected', () => {
    fakeConfig.context.identities.orcid.connected = false;

    const { elements } = createWrapper();

    assert.isFalse(elements.showOrcidIdCheckbox.exists());
  });

  it('doesn\t render the show-orcid-id checkbox if the orcid feature flag is disabled', () => {
    fakeConfig.context.identities.orcid.connected = true;
    fakeConfig.features.log_in_with_orcid = false;

    const { elements } = createWrapper();

    assert.isFalse(elements.showOrcidIdCheckbox.exists());
  });

  [true, false].forEach(showOrcidId => {
    it('initially renders the show-orcid-id checkbox as checked or un-checked depending on the config', () => {
      fakeConfig.context.identities.orcid.connected = true;
      fakeConfig.context.user.preferences.show_orcid_id_on_profile =
        showOrcidId;

      const { elements } = createWrapper();

      assert.equal(elements.showOrcidIdCheckbox.prop('checked'), showOrcidId);
    });
  });

  [true, false].forEach(initialCheckboxValue => {
    it('sends API request when show-orcid-id checkbox clicked', () => {
      fakeConfig.context.identities.orcid.connected = true;
      fakeConfig.context.user.preferences.show_orcid_id_on_profile =
        initialCheckboxValue;
      fakeCallAPI.resolves({
        preferences: { show_orcid_id_on_profile: !initialCheckboxValue },
      });

      const { elements } = createWrapper();

      elements.showOrcidIdCheckbox.find('input').getDOMNode().checked =
        !initialCheckboxValue;
      elements.showOrcidIdCheckbox.find('input').simulate('change');

      assert.calledOnceWithExactly(
        fakeCallAPI,
        fakeConfig.api.updateUserPrefs.url,
        {
          method: fakeConfig.api.updateUserPrefs.method,
          headers: fakeConfig.api.updateUserPrefs.headers,
          json: {
            preferences: { show_orcid_id_on_profile: !initialCheckboxValue },
          },
        },
      );
    });
  });

  it('handles errors from the update-user-prefs APO', () => {
    fakeConfig.context.identities.orcid.connected = true;
    fakeCallAPI.rejects();

    const { elements } = createWrapper();

    elements.showOrcidIdCheckbox.find('input').simulate('change');
  });

  it(
    'passes a11y checks',
    checkAccessibility({ content: () => createWrapper().wrapper }),
  );
});
