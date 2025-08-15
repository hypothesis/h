import { Button } from '@hypothesis/frontend-shared';
import { ExternalIcon } from '@hypothesis/frontend-shared';
import { useContext } from 'preact/hooks';

import { LoginFormsConfig } from '../config';
import type { AccountSettingsConfigObject } from '../config';
import Form from '../forms-common/components/Form';
import FormContainer from '../forms-common/components/FormContainer';
import TextField from '../forms-common/components/TextField';
import { useFormValue } from '../forms-common/form-value';
import type { FormValue } from '../forms-common/form-value';
import FacebookIcon from './FacebookIcon';
import GoogleIcon from './GoogleIcon';
import ORCIDIcon from './ORCIDIcon';

const textFieldProps = (field: FormValue<string>) => ({
  value: field.value,
  fieldError: field.error,
  onChangeValue: field.update,
  onCommitValue: field.commit,
});

function Heading({ text }: { text: string }) {
  return <h1 class="text-lg mb-4">{text}</h1>;
}

function FormSubmitButton() {
  return (
    <div className="mb-8 pt-2 flex items-center gap-x-4">
      <div className="grow" />
      <Button type="submit" variant="primary" data-testid="submit-button">
        Save
      </Button>
    </div>
  );
}

function ChangeEmailForm({ config }: { config: AccountSettingsConfigObject }) {
  const email = useFormValue(config.forms.email, 'email', '');
  const password = useFormValue(config.forms.email, 'password', '');
  const heading = config.context.user.email
    ? 'Change your email address'
    : 'Add an email address';

  return (
    <FormContainer>
      <Heading text={heading} />

      <Form csrfToken={config.csrfToken} data-testid="email-form">
        <input type="hidden" name="__formid__" value="email" />

        {config.context.user.email && (
          <p>
            Current email address:{' '}
            <b data-testid="current-email">{config.context.user.email}</b>
          </p>
        )}
        <TextField
          name="email"
          inputType="email"
          label={
            config.context.user.email ? 'New email address' : 'Email address'
          }
          required={true}
          {...textFieldProps(email)}
        />
        {config.context.user.has_password && (
          <TextField
            name="password"
            label="Confirm password"
            inputType="password"
            required={true}
            {...textFieldProps(password)}
          />
        )}
        <FormSubmitButton />
      </Form>
    </FormContainer>
  );
}

function ChangePasswordForm({
  config,
}: {
  config: AccountSettingsConfigObject;
}) {
  const password = useFormValue(config.forms.password, 'password', '');
  const newPassword = useFormValue(config.forms.password, 'new_password', '');
  const newPasswordConfirm = useFormValue(
    config.forms.password,
    'new_password_confirm',
    '',
  );

  return (
    <FormContainer>
      {config.context.user.has_password ? (
        <Heading text="Change your password" />
      ) : (
        <Heading text="Add a password" />
      )}

      <Form csrfToken={config.csrfToken} data-testid="password-form">
        <input type="hidden" name="__formid__" value="password" />
        {config.context.user.has_password && (
          <TextField
            name="password"
            label="Current password"
            inputType="password"
            required={true}
            {...textFieldProps(password)}
          />
        )}
        <TextField
          name="new_password"
          label="New password"
          inputType="password"
          required={true}
          minLength={8}
          {...textFieldProps(newPassword)}
        />
        <TextField
          name="new_password_confirm"
          label="Confirm new password"
          inputType="password"
          required={true}
          {...textFieldProps(newPasswordConfirm)}
        />
        <FormSubmitButton />
      </Form>
    </FormContainer>
  );
}

// <ConnectAccountButton/> is similar to <SocialLoginLink/> but with some
// differences: it has two modes and can either indicate an already-connected
// account or can act as a button for connecting an account.
function ConnectAccountButton({
  config,
  provider,
}: {
  config: AccountSettingsConfigObject;
  provider: 'facebook' | 'google' | 'orcid';
}) {
  const providerConfig = config.context.identities?.[provider];
  const connected = providerConfig?.connected;
  const providerUniqueID = providerConfig?.provider_unique_id;
  const email = providerConfig?.email;
  const providerURL = providerConfig?.url;
  const connectURL = config.routes?.[`oidc.connect.${provider}`];
  const Icon = {
    google: GoogleIcon,
    facebook: FacebookIcon,
    orcid: ORCIDIcon,
  }[provider];
  const label = {
    google: (
      <>
        Connect <b>Google</b>
      </>
    ),
    facebook: (
      <>
        Connect <b>Facebook</b>
      </>
    ),
    orcid: (
      <>
        Connect <b>ORCID</b>
      </>
    ),
  }[provider];

  return (
    <>
      {connected ? (
        <div className="border rounded-md px-3 py-2 flex flex-row items-center gap-x-3">
          <Icon />
          <span className="grow">
            Connected:{' '}
            <a
              target="_blank"
              rel="noreferrer"
              class="font-bold"
              href={providerURL}
              data-testid={`connect-account-link-${provider}`}
            >
              {email || providerUniqueID}
            </a>
          </span>
          <Form
            csrfToken={config.csrfToken}
            action={config.routes.identity_delete}
            data-testid={`remove-account-form-${provider}`}
          >
            <input type="hidden" name="provider" value={provider} />
            <input
              type="hidden"
              name="provider_unique_id"
              value={providerUniqueID}
            />
            <Button type="submit" size="sm">
              Remove
            </Button>
          </Form>
        </div>
      ) : (
        <a
          href={connectURL}
          className="border rounded-md p-3 flex flex-row items-center gap-x-3"
          data-testid={`connect-account-link-${provider}`}
        >
          <Icon />
          <span className="grow">{label}</span>
          <ExternalIcon className="w-[20px] h-[20px]" />
        </a>
      )}
    </>
  );
}

function ConnectAccountButtons({
  config,
}: {
  config: AccountSettingsConfigObject;
}) {
  if (
    !(
      config.features.log_in_with_google ||
      config.features.log_in_with_facebook ||
      config.features.log_in_with_orcid
    )
  ) {
    return null;
  }

  return (
    <FormContainer>
      <Heading text="Connect your account" />

      <p className="mb-9">
        Connecting an account enables you to log in to Hypothesis without your
        Hypothesis password.
      </p>

      <div class="mx-auto max-w-[400px] flex flex-col gap-y-3">
        {config.features.log_in_with_google && (
          <ConnectAccountButton config={config} provider="google" />
        )}
        {config.features.log_in_with_facebook && (
          <ConnectAccountButton config={config} provider="facebook" />
        )}
        {config.features.log_in_with_orcid && (
          <ConnectAccountButton config={config} provider="orcid" />
        )}
      </div>
    </FormContainer>
  );
}

export default function AccountSettingsForms() {
  const config = useContext(LoginFormsConfig) as AccountSettingsConfigObject;

  return (
    <>
      <ChangeEmailForm config={config} />
      <ChangePasswordForm config={config} />
      <ConnectAccountButtons config={config} />
    </>
  );
}
