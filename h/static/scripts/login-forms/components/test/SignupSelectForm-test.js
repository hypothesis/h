import { mount } from '@hypothesis/frontend-testing';

import { Config } from '../../config';
import { routes } from '../../routes';
import SignupSelectForm from '../SignupSelectForm';

describe('SignupSelectForm', () => {
  let fakeConfig;

  function createComponent() {
    return mount(
      <Config.Provider value={fakeConfig}>
        <SignupSelectForm />
      </Config.Provider>,
    );
  }

  beforeEach(() => {
    fakeConfig = {
      features: {
        log_in_with_facebook: false,
        log_in_with_google: false,
        log_in_with_orcid: false,
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

  it('renders email signup link', () => {
    const wrapper = createComponent();
    const emailLink = wrapper.find(`a[href="${routes.signupWithEmail}"]`);
    assert.isTrue(emailLink.exists());
    assert.include(emailLink.text(), 'Sign up with email');
  });

  ['google', 'facebook', 'orcid'].forEach(provider => {
    it(`renders ${provider} signup link if feature enabled`, () => {
      const href = `https://example.com/oidc/login/${provider}`;
      fakeConfig.urls.login = {
        [provider]: href,
      };

      const wrapper = createComponent();

      const link = wrapper.find('SocialLoginLink');
      assert.isTrue(link.exists());
      assert.equal(link.prop('provider'), provider);
      assert.equal(link.prop('href'), href);
    });
  });
});
