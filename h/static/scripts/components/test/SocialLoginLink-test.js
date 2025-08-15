import { mount } from '@hypothesis/frontend-testing';

import { LoginFormsConfig } from '../../config';
import SocialLoginLink from '../SocialLoginLink';

describe('SocialLoginLink', () => {
  let fakeConfig;

  beforeEach(() => {
    fakeConfig = {
      urls: {
        login: {
          facebook: '/oidc/login/facebook',
          google: '/oidc/login/google',
          orcid: '/oidc/login/orcid',
        },
      },
    };
  });

  [
    {
      provider: 'google',
      text: 'Continue with Google',
    },
    {
      provider: 'facebook',
      text: 'Continue with Facebook',
    },
    {
      provider: 'orcid',
      text: 'Continue with ORCID',
    },
  ].forEach(({ provider, text }) => {
    it(`renders ${provider} signup link with correct href`, () => {
      const href = fakeConfig.urls.login[provider];
      const wrapper = mount(
        <LoginFormsConfig.Provider value={fakeConfig}>
          <SocialLoginLink provider={provider} href={href} />
        </LoginFormsConfig.Provider>,
      );

      const link = wrapper.find(`a[href="${href}"]`);
      assert.isTrue(link.exists());
      assert.include(link.text(), text);
    });
  });
});
