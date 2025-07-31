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
    };
  });

  [
    {
      provider: 'email',
      link: routes.signupWithEmail,
      text: 'Sign up with email',
    },
    {
      provider: 'Google',
      link: routes.loginWithGoogle,
      text: 'Continue with Google',
      features: {
        log_in_with_google: true,
      },
    },
    {
      provider: 'Facebook',
      link: routes.loginWithFacebook,
      text: 'Continue with Facebook',
      features: {
        log_in_with_facebook: true,
      },
    },
    {
      provider: 'ORCID',
      link: routes.loginWithORCID,
      text: 'Continue with ORCID',
      features: {
        log_in_with_orcid: true,
      },
    },
  ].forEach(({ provider, link, text, features = {} }) => {
    it(`renders ${provider} signup link with correct href`, () => {
      fakeConfig.features = features;

      const wrapper = createComponent();

      const emailLink = wrapper.find(`a[href="${link}"]`);
      assert.isTrue(emailLink.exists());
      assert.include(emailLink.text(), text);
    });
  });
});
