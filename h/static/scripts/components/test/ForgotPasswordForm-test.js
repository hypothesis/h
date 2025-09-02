import { checkAccessibility, mount } from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';

import { LoginFormsConfig } from '../../config';
import { $imports, default as ForgotPasswordForm } from '../ForgotPasswordForm';

describe('ForgotPasswordForm', () => {
  let fakeConfig;

  beforeEach(() => {
    fakeConfig = {
      csrfToken: 'fake-csrf-token',
      form: {
        data: {
          email: '',
        },
        errors: {},
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
      emailField: wrapper.find('TextField[name="email"]'),
    };
  };

  const createWrapper = (props = {}) => {
    const wrapper = mount(
      <LoginFormsConfig.Provider value={fakeConfig}>
        <ForgotPasswordForm {...props} />
      </LoginFormsConfig.Provider>,
    );
    const elements = getElements(wrapper);
    return { wrapper, elements };
  };

  it('uses CSRF token from config', () => {
    const { elements } = createWrapper();
    assert.equal(elements.csrfInput.prop('value'), fakeConfig.csrfToken);
  });

  it('pre-fills fields from config data', () => {
    fakeConfig.form.data.email = 'test@example.com';
    const { elements } = createWrapper();
    assert.equal(elements.emailField.prop('value'), 'test@example.com');
  });

  it('updates email value when onChangeValue is called', () => {
    const { wrapper, elements } = createWrapper();
    const newEmail = 'user@example.com';

    act(() => {
      elements.emailField.prop('onChangeValue')(newEmail);
    });
    wrapper.update();
    const updatedElements = getElements(wrapper);

    assert.equal(updatedElements.emailField.prop('value'), newEmail);
  });

  it('displays field errors from config', () => {
    fakeConfig.form.errors.email = 'Invalid email address';

    const { elements } = createWrapper();

    assert.equal(
      elements.emailField.prop('fieldError'),
      'Invalid email address',
    );
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: () => createWrapper().wrapper }),
  );
});
