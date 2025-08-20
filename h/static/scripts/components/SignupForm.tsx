import { Button, CheckIcon } from '@hypothesis/frontend-shared';
import { useContext, useLayoutEffect, useState } from 'preact/hooks';

import { LoginFormsConfig } from '../config';
import type { SignupConfigObject } from '../config';
import { useFormValue } from '../util/form-value';
import Checkbox from './Checkbox';
import FacebookIcon from './FacebookIcon';
import Form from './Form';
import FormContainer from './FormContainer';
import FormHeader from './FormHeader';
import GoogleIcon from './GoogleIcon';
import ORCIDIcon from './ORCIDIcon';
import SignupFooter from './SignupFooter';
import TextField from './TextField';

type IdProviderBadgeProps = {
  provider: IdProvider;
  identity: string;
};

/**
 * Box indicating the OIDC / social login identity being associated with a
 * Hypothesis account.
 */
function IdProviderBadge({ provider, identity }: IdProviderBadgeProps) {
  return (
    <div
      data-testid="id-badge"
      className="border rounded-md p-3 flex flex-row items-center gap-x-3 max-w-[400px] mx-auto"
    >
      {provider === 'facebook' && (
        <FacebookIcon className="inline" aria-label="Facebook icon" />
      )}
      {provider === 'google' && (
        <GoogleIcon className="inline" aria-label="Google icon" />
      )}
      {provider === 'orcid' && (
        <a href="https://orcid.org" target="_blank" rel="noreferrer">
          <ORCIDIcon className="inline" aria-label="ORCID icon" />
        </a>
      )}{' '}
      <span className="grow">
        Connected: <b data-testid="connected-id">{identity}</b>
      </span>
      <CheckIcon className="w-[20px] h-[20px]" />
    </div>
  );
}

/** Supported ID providers for OIDC-based login. */
export type IdProvider = 'facebook' | 'google' | 'orcid';

export type SignupFormProps = {
  /**
   * Identity provider if using OIDC / social login.
   *
   * When this prop is set there should also be:
   *
   *  - An `identity` field in the config for the page
   *  - An `idinfo` query parameter
   */
  idProvider?: IdProvider;

  // Test seams
  location_?: Location;
};

export default function SignupForm({
  idProvider,
  location_ = location,
}: SignupFormProps) {
  const config = useContext(LoginFormsConfig) as SignupConfigObject;
  const [submitted, setSubmitted] = useState(false);
  const [idInfoJWT, setIdInfoJWT] = useState<string | null>(null);
  const form = config.form;

  const username = useFormValue(form, 'username', '', {
    validate: (username, committed) => {
      if (!username.match(/^[A-Za-z0-9_.]*$/)) {
        return 'Must have only letters, numbers, periods and underscores.';
      }
      if (committed && (username.startsWith('.') || username.endsWith('.'))) {
        return 'May not start or end with a period.';
      }
      return undefined;
    },
  });
  const email = useFormValue(form, 'email', '');
  const password = useFormValue(form, 'password', '');
  const privacyAccepted = useFormValue(form, 'privacy_accepted', false);
  const commsOptIn = useFormValue(form, 'comms_opt_in', false);

  useLayoutEffect(() => {
    const url = new URL(location_.href);
    const idInfo = url.searchParams.get('idinfo');
    if (!idInfo) {
      return;
    }
    setIdInfoJWT(idInfo);
  }, [location_]);

  // When visiting social login signup page the server should ensure the "idinfo"
  // JWT is always present, so the user should never see this. Show a unique
  // error to aid debugging in case it does ever happen.
  if (idProvider && !idInfoJWT) {
    return (
      <div data-testid="error">
        Social login identity missing. Please try again.
      </div>
    );
  }

  return (
    <>
      <FormHeader center={config.forOAuth}>Sign up for Hypothesis</FormHeader>
      <FormContainer>
        <Form csrfToken={config.csrfToken} onSubmit={() => setSubmitted(true)}>
          {idProvider && config.identity && (
            <IdProviderBadge
              provider={idProvider}
              identity={
                config.identity.email || config.identity.provider_unique_id
              }
            />
          )}
          {idInfoJWT && <input type="hidden" name="idinfo" value={idInfoJWT} />}
          <TextField
            type="input"
            name="username"
            value={username.value}
            fieldError={username.error}
            onChangeValue={username.update}
            onCommitValue={username.commit}
            label="Username"
            minLength={3}
            maxLength={30}
            autofocus
            required
            showRequired={false}
          />
          {!idProvider && (
            <TextField
              type="input"
              name="email"
              value={email.value}
              fieldError={email.error}
              onChangeValue={email.update}
              label="Email address"
              required
              showRequired={false}
            />
          )}
          {!idProvider && (
            <TextField
              type="input"
              inputType="password"
              name="password"
              value={password.value}
              fieldError={password.error}
              onChangeValue={password.update}
              label="Password"
              minLength={8}
              required
              showRequired={false}
            />
          )}
          {
            // When using social login, the username field is the last input.
            // This has a character counter below it. Add a margin between the
            // counter and the next line.
            idProvider && <div className="mt-3" />
          }
          <Checkbox
            data-testid="privacy-accepted"
            checked={privacyAccepted.value}
            name="privacy_accepted"
            // Backend form validation expects the string "true" rather than the
            // HTML form default of "on".
            value="true"
            onChange={e => {
              privacyAccepted.update((e.target as HTMLInputElement).checked);
            }}
            error={privacyAccepted.error}
            required
          >
            I have read and agree to the{' '}
            <a className="link" href="https://web.hypothes.is/privacy/">
              privacy policy
            </a>
            ,{' '}
            <a
              className="link"
              href="https://web.hypothes.is/terms-of-service/"
            >
              terms of service
            </a>
            , and{' '}
            <a
              className="link"
              href="https://web.hypothes.is/community-guidelines/"
            >
              community guidelines
            </a>
            .
          </Checkbox>
          <Checkbox
            data-testid="comms-opt-in"
            checked={commsOptIn.value}
            name="comms_opt_in"
            // Backend form validation expects the string "true" rather than the
            // HTML form default of "on".
            value="true"
            onChange={e => {
              commsOptIn.update((e.target as HTMLInputElement).checked);
            }}
          >
            I would like to receive news about annotation and Hypothesis.
          </Checkbox>
          <div className="pt-2 flex items-center gap-x-4">
            <div className="grow" />
            <Button
              type="submit"
              variant="primary"
              data-testid="submit-button"
              // Prevent duplicate signup attempts.
              // See https://github.com/hypothesis/h/pull/3851
              disabled={submitted}
            >
              Sign up
            </Button>
          </div>
        </Form>
      </FormContainer>
      <SignupFooter action="login" />
    </>
  );
}
