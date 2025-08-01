import { routes } from '../routes';
import FacebookIcon from './FacebookIcon';
import GoogleIcon from './GoogleIcon';
import LoginLink from './LoginLink';
import ORCIDIcon from './ORCIDIcon';

const providerInfo = {
  google: {
    href: routes.loginWithGoogle,
    text: (
      <>
        Continue with <b>Google</b>
      </>
    ),
    Icon: GoogleIcon,
  },
  facebook: {
    href: routes.loginWithFacebook,
    text: (
      <>
        Continue with <b>Facebook</b>
      </>
    ),
    Icon: FacebookIcon,
  },
  orcid: {
    href: routes.loginWithORCID,
    text: (
      <>
        Continue with <b>ORCID</b>
      </>
    ),
    Icon: ORCIDIcon,
  },
};

export type SocialLoginLinkProps = {
  provider: 'google' | 'facebook' | 'orcid';
};

/** Sign-up / login link for an external identity provider. */
export default function SocialLoginLink({ provider }: SocialLoginLinkProps) {
  const info = providerInfo[provider];
  return (
    <LoginLink href={info.href} providerIcon={<info.Icon className="inline" />}>
      {info.text}
    </LoginLink>
  );
}
