import { mount } from '@hypothesis/frontend-testing';

import { routes } from '../../routes';
import SocialLoginLink from '../SocialLoginLink';

describe('SocialLoginLink', () => {
  [
    {
      provider: 'google',
      href: routes.loginWithGoogle,
      text: 'Continue with Google',
    },
    {
      provider: 'facebook',
      href: routes.loginWithFacebook,
      text: 'Continue with Facebook',
    },
    {
      provider: 'orcid',
      href: routes.loginWithORCID,
      text: 'Continue with ORCID',
    },
  ].forEach(({ provider, href, text }) => {
    it(`renders ${provider} signup link with correct href`, () => {
      const wrapper = mount(<SocialLoginLink provider={provider} />);

      const link = wrapper.find(`a[href="${href}"]`);
      assert.isTrue(link.exists());
      assert.include(link.text(), text);
    });
  });
});
