import { mount } from '@hypothesis/frontend-testing';

import { Config } from '../../config';
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
      const wrapper = mount(
        <Config.Provider value={fakeConfig}>
          <SocialLoginLink provider={provider} />
        </Config.Provider>,
      );

      const link = wrapper.find(`a[href="${fakeConfig.urls.login[provider]}"]`);
      assert.isTrue(link.exists());
      assert.include(link.text(), text);
    });
  });
});
