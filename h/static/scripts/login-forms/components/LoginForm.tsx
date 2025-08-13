import { Button, Link, LogoIcon } from '@hypothesis/frontend-shared';
import { useContext } from 'preact/hooks';

import Form from '../../forms-common/components/Form';
import FormContainer from '../../forms-common/components/FormContainer';
import FormHeader from '../../forms-common/components/FormHeader';
import TextField from '../../forms-common/components/TextField';
import { useFormValue } from '../../forms-common/form-value';
import { Config } from '../config';
import type { LoginConfigObject } from '../config';
import { routes } from '../routes';
import SignupFooter from './SignupFooter';
import SocialLoginLink from './SocialLoginLink';

export type LoginFormProps = {
  enableSocialLogin: boolean;
};

export default function LoginForm({ enableSocialLogin }: LoginFormProps) {
  const config = useContext(Config) as LoginConfigObject;
  const form = config.form;

  const username = useFormValue(form, 'username', '');
  const password = useFormValue(form, 'password', '');

  // In the OAuth window we include "with Hypothesis" and a logo to make it
  // more obvious which credentials are expected, as this is less obvious than
  // when visiting the website directly.
  const title = config.forOAuth ? (
    <>
      Log in to Hypothesis{' '}
      <LogoIcon className="inline ml-1 w-[28px] h-[28px]" />
    </>
  ) : (
    'Log in'
  );

  // Auto-focus the username, unless it was pre-filled (eg. as a result of
  // following an activation link).
  const autofocusUsername =
    Boolean(username.error) || username.value.length === 0;

  return (
    <>
      <FormHeader center={config.forOAuth}>{title}</FormHeader>
      <FormContainer
        // The max width here and item gap should match SignupSelectForm.
        //
        // This keeps the positioning of items consistent if the user navigates
        // from the login page to the signup page.
        classes="mx-auto max-w-[400px] flex flex-col gap-y-3 items-stretch"
      >
        <Form
          csrfToken={config.csrfToken}
          // Remove `mx-auto` from this form since it is applied to the parent.
          center={false}
        >
          <TextField
            type="input"
            name="username"
            value={username.value}
            fieldError={username.error}
            onChangeValue={username.update}
            label="Username or email"
            autofocus={autofocusUsername}
            required
            showRequired={false}
          />
          <TextField
            type="input"
            inputType="password"
            name="password"
            value={password.value}
            fieldError={password.error}
            onChangeValue={password.update}
            label="Password"
            autofocus={!autofocusUsername}
            required
            showRequired={false}
          />
          <div className="pt-2 flex flex-row items-center">
            <Link
              href={routes.forgotPassword}
              underline="always"
              variant="text-light"
              data-testid="forgot-password-link"
            >
              Forgot your password?
            </Link>
            <div className="grow" />
            <Button type="submit" variant="primary" data-testid="submit-button">
              Log in
            </Button>
          </div>
        </Form>
        {enableSocialLogin && (
          <>
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
              <SocialLoginLink
                provider="orcid"
                href={config.urls.login.orcid}
              />
            )}
          </>
        )}
      </FormContainer>
      <SignupFooter action="signup" />
    </>
  );
}
