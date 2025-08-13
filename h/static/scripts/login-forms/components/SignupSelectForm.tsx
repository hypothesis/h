import { EmailFilledIcon } from '@hypothesis/frontend-shared';
import { useContext } from 'preact/hooks';

import FormHeader from '../../forms-common/components/FormHeader';
import { Config } from '../config';
import type { SignupConfigObject } from '../config';
import { routes } from '../routes';
import LoginLink from './LoginLink';
import SignupFooter from './SignupFooter';
import SocialLoginLink from './SocialLoginLink';

/**
 * Form for the first page of the signup flow which gives users a list of
 * identity providers to choose from.
 */
export default function SignupSelectForm() {
  const config = useContext(Config) as SignupConfigObject;

  // nb. Options for social login are listed in descending order of expected
  // usage rather than alphabetically.
  return (
    <>
      <div className="flex flex-col text-md">
        <FormHeader center={config.forOAuth}>Sign up for Hypothesis</FormHeader>
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
          {config.urls.login.google && (
            <SocialLoginLink
              provider="google"
              href={config.urls.login.google}
            />
          )}
          {config.urls.login.facebook && (
            <SocialLoginLink
              provider="facebook"
              href={config.urls.login.facebook}
            />
          )}
          {config.urls.login.orcid && (
            <SocialLoginLink provider="orcid" href={config.urls.login.orcid} />
          )}
        </div>
      </div>
      <SignupFooter action="login" />
    </>
  );
}
