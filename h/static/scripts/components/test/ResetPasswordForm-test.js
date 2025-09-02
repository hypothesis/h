import { checkAccessibility, mount } from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';

import { LoginFormsConfig } from '../../config';
import { $imports, default as ResetPasswordForm } from '../ResetPasswordForm';

describe('ResetPasswordForm', () => {
  let fakeConfig;

  beforeEach(() => {
    fakeConfig = {
      csrfToken: 'fake-csrf-token',
      form: {
        data: {
          user: '',
          password: '',
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
      resetCodeField: wrapper.find('TextField[name="email"]'),
      passwordField: wrapper.find('TextField[name="password"]'),
    };
  };

  const createWrapper = (props = {}) => {
    const wrapper = mount(
      <LoginFormsConfig.Provider value={fakeConfig}>
        <ResetPasswordForm {...props} />
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
    fakeConfig.form.data.user = 'reset123';
    fakeConfig.form.data.password = 'initialpass';

    const { elements } = createWrapper();

    assert.equal(elements.resetCodeField.prop('value'), 'reset123');
    assert.equal(elements.passwordField.prop('value'), 'initialpass');
  });

  it('updates reset code value when onChangeValue is called', () => {
    const { wrapper, elements } = createWrapper();
    const newCode = 'newreset456';

    act(() => {
      elements.resetCodeField.prop('onChangeValue')(newCode);
    });
    wrapper.update();
    const updatedElements = getElements(wrapper);

    assert.equal(updatedElements.resetCodeField.prop('value'), newCode);
  });

  it('updates password value when onChangeValue is called', () => {
    const { wrapper, elements } = createWrapper();
    const newPassword = 'newpassword123';

    act(() => {
      elements.passwordField.prop('onChangeValue')(newPassword);
    });
    wrapper.update();
    const updatedElements = getElements(wrapper);

    assert.equal(updatedElements.passwordField.prop('value'), newPassword);
  });

  it('displays field errors from config', () => {
    fakeConfig.form.errors.user = 'Invalid reset code';
    fakeConfig.form.errors.password = 'Password too short';

    const { elements } = createWrapper();

    assert.equal(
      elements.resetCodeField.prop('fieldError'),
      'Invalid reset code',
    );
    assert.equal(
      elements.passwordField.prop('fieldError'),
      'Password too short',
    );
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: () => createWrapper().wrapper }),
  );
});
