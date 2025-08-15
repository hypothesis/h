import { EmailFilledIcon } from '@hypothesis/frontend-shared';
import { useContext } from 'preact/hooks';

import { LoginFormsConfig } from '../config';
import type { SignupConfigObject } from '../config';
import FormHeader from '../forms-common/components/FormHeader';
import { routes } from '../routes';
import LoginLink from './LoginLink';
import SignupFooter from './SignupFooter';
import SocialLoginLink from './SocialLoginLink';

/**
 * Form for the first page of the signup flow which gives users a list of
 * identity providers to choose from.
 */
export default function SignupSelectForm() {
  const config = useContext(LoginFormsConfig) as SignupConfigObject;

  const loginURLs = config.urls?.login;

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
          {loginURLs && (
            <>
              <div className="self-center uppercase">or</div>
              {loginURLs.google && (
                <SocialLoginLink provider="google" href={loginURLs.google} />
              )}
              {loginURLs.facebook && (
                <SocialLoginLink
                  provider="facebook"
                  href={loginURLs.facebook}
                />
              )}
              {loginURLs.orcid && (
                <SocialLoginLink provider="orcid" href={loginURLs.orcid} />
              )}
            </>
          )}
        </div>
      </div>
      <SignupFooter action="login" />
    </>
  );
}
