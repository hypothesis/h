import { mount } from '@hypothesis/frontend-testing';

import { Config } from '../../config';
import SignupFooter from '../SignupFooter';

describe('SignupFooter', () => {
  let fakeConfig;

  function createComponent(props = {}) {
    return mount(
      <Config.Provider value={fakeConfig}>
        <SignupFooter action="login" {...props} />
      </Config.Provider>,
    );
  }

  beforeEach(() => {
    fakeConfig = {
      forOAuth: false,
      urls: {
        login: {
          username_or_email: '/login',
        },
        signup: '/signup',
      },
    };
  });

  it('renders footer if login URL is present', () => {
    const wrapper = createComponent({ action: 'login' });
    assert.isTrue(wrapper.exists('footer'));
  });

  it('renders nothing if login URL is missing', () => {
    delete fakeConfig.urls;
    const wrapper = createComponent({ action: 'login' });
    assert.isFalse(wrapper.exists('footer'));
  });

  describe('when action is "login"', () => {
    it('renders login link with correct href', () => {
      const wrapper = createComponent({ action: 'login' });
      const loginLink = wrapper.find('a[data-testid="login-link"]');
      assert.isTrue(loginLink.exists());
      assert.equal(loginLink.prop('href'), '/login');
    });

    it('does not render signup link', () => {
      const wrapper = createComponent({ action: 'login' });
      const signupLink = wrapper.find('a[data-testid="signup-link"]');
      assert.isFalse(signupLink.exists());
    });
  });

  describe('when action is "signup"', () => {
    it('renders signup link with correct href', () => {
      const wrapper = createComponent({ action: 'signup' });
      const signupLink = wrapper.find('a[data-testid="signup-link"]');
      assert.isTrue(signupLink.exists());
      assert.equal(signupLink.prop('href'), '/signup');
    });

    it('does not render login link', () => {
      const wrapper = createComponent({ action: 'signup' });
      const loginLink = wrapper.find('a[data-testid="login-link"]');
      assert.isFalse(loginLink.exists());
    });
  });

  describe('styling', () => {
    it('applies OAuth styling when forOAuth is true', () => {
      fakeConfig.forOAuth = true;
      const wrapper = createComponent();
      const footer = wrapper.find('footer');
      assert.include(footer.prop('className'), 'fixed');
    });

    it('applies default styling when forOAuth is false', () => {
      fakeConfig.forOAuth = false;
      const wrapper = createComponent();
      const footer = wrapper.find('footer');
      assert.notInclude(footer.prop('className'), 'fixed');
    });
  });
});
