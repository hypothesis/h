import {
  ArrowRightIcon,
  EmailFilledIcon,
  ExternalIcon,
} from '@hypothesis/frontend-shared';
import type { ComponentChildren } from 'preact';
import { useContext } from 'preact/hooks';
import { Link as RouterLink } from 'wouter-preact';

import FormHeader from '../../forms-common/components/FormHeader';
import { Config } from '../config';
import { routes } from '../routes';
import GoogleIcon from './GoogleIcon';
import ORCIDIcon from './ORCIDIcon';

type SocialSignupLinkProps = {
  /** True if this navigation is handled client-side. */
  routerLink?: boolean;

  /** Target URL for the link. */
  href: string;

  /** Icon for the identity provider. */
  providerIcon: ComponentChildren;

  /** Text for the link. */
  children: ComponentChildren;
};

function SignupLink({
  routerLink,
  href,
  providerIcon,
  children,
}: SocialSignupLinkProps) {
  const LinkType = routerLink ? RouterLink : 'a';
  const NavigateIcon = routerLink ? ArrowRightIcon : ExternalIcon;

  return (
    <LinkType
      href={href}
      className="border rounded-md p-3 flex flex-row items-center gap-x-3"
    >
      {providerIcon}
      <span className="grow">{children}</span>
      <NavigateIcon className="w-[20px] h-[20px]" />
    </LinkType>
  );
}

/**
 * Form for the first page of the signup flow which gives users a list of
 * identity providers to choose from.
 */
export default function SignupSelectForm() {
  const config = useContext(Config)!;

  return (
    <div className="flex flex-col text-md">
      <FormHeader>Sign up for Hypothesis</FormHeader>
      <div
        // Top margin intended to give roughly even spacing above and below the
        // provider list.
        className="mt-[40px] self-center flex flex-col gap-y-3 text-grey-7 w-[400px]"
      >
        <SignupLink
          routerLink={true}
          href={routes.signupWithEmail}
          providerIcon={
            // Expand icon size to 24px to match other provider icons.
            <EmailFilledIcon className="inline w-[24px] h-[24px]" />
          }
        >
          Sign up with <b>email</b>
        </SignupLink>
        <div className="self-center uppercase">or</div>
        {config.features.log_in_with_google && (
          <SignupLink
            href={routes.loginWithGoogle}
            providerIcon={<GoogleIcon className="inline" />}
          >
            Continue with <b>Google</b>
          </SignupLink>
        )}
        {config.features.log_in_with_orcid && (
          <SignupLink
            href={routes.loginWithORCID}
            providerIcon={<ORCIDIcon className="inline" />}
          >
            Continue with <b>ORCID</b>
          </SignupLink>
        )}
      </div>
    </div>
  );
}
