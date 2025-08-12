import FacebookIcon from './FacebookIcon';
import GoogleIcon from './GoogleIcon';
import LoginLink from './LoginLink';
import ORCIDIcon from './ORCIDIcon';

const providerInfo = {
  google: {
    text: (
      <>
        Continue with <b>Google</b>
      </>
    ),
    Icon: GoogleIcon,
  },
  facebook: {
    text: (
      <>
        Continue with <b>Facebook</b>
      </>
    ),
    Icon: FacebookIcon,
  },
  orcid: {
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
  href: string;
};

/** Sign-up / login link for an external identity provider. */
export default function SocialLoginLink({
  provider,
  href,
}: SocialLoginLinkProps) {
  const info = providerInfo[provider];
  return (
    <LoginLink href={href} providerIcon={<info.Icon className="inline" />}>
      {info.text}
    </LoginLink>
  );
}
