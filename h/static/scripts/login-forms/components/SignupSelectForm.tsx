import { EmailFilledIcon } from '@hypothesis/frontend-shared';
import { useContext } from 'preact/hooks';

import FormHeader from '../../forms-common/components/FormHeader';
import { Config } from '../config';
import { routes } from '../routes';
import LoginLink from './LoginLink';
import SocialLoginLink from './SocialLoginLink';

/**
 * Form for the first page of the signup flow which gives users a list of
 * identity providers to choose from.
 */
export default function SignupSelectForm() {
  const config = useContext(Config)!;

  // nb. Options for social login are listed in descending order of expected
  // usage rather than alphabetically.
  return (
    <div className="flex flex-col text-md">
      <FormHeader>Sign up for Hypothesis</FormHeader>
      <div
        // Top margin intended to give roughly even spacing above and below the
        // provider list.
        className="mt-[40px] self-center flex flex-col gap-y-3 text-grey-7 w-[400px]"
      >
        <LoginLink
          routerLink={true}
          href={routes.signupWithEmail}
          providerIcon={
            // Expand icon size to 24px to match other provider icons.
            <EmailFilledIcon className="inline w-[24px] h-[24px]" />
          }
        >
          Sign up with <b>email</b>
        </LoginLink>
        <div className="self-center uppercase">or</div>
        {config.features.log_in_with_google && (
          <SocialLoginLink provider="google" />
        )}
        {config.features.log_in_with_facebook && (
          <SocialLoginLink provider="facebook" />
        )}
        {config.features.log_in_with_orcid && (
          <SocialLoginLink provider="orcid" />
        )}
      </div>
    </div>
  );
}
