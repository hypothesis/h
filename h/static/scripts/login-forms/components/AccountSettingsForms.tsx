import { Button } from '@hypothesis/frontend-shared';
import { ExternalIcon, CheckIcon } from '@hypothesis/frontend-shared';
import { useContext } from 'preact/hooks';

import Form from '../../forms-common/components/Form';
import FormContainer from '../../forms-common/components/FormContainer';
import TextField from '../../forms-common/components/TextField';
import { useFormValue } from '../../forms-common/form-value';
import type { FormValue } from '../../forms-common/form-value';
import { Config } from '../config';
import type { AccountSettingsConfigObject } from '../config';
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

  return (
    <FormContainer>
      {config.context.user.email ? (
        <Heading text="Change your email address" />
      ) : (
        <Heading text="Add an email address" />
      )}

      <Form csrfToken={config.csrfToken} data-testid="email-form">
        <input type="hidden" name="__formid__" value="email" />
        <TextField
          name="email"
          label="Email address"
          placeholder={config.context.user?.email}
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
        <a
          href={providerURL}
          className="border rounded-md p-3 flex flex-row items-center gap-x-3"
          data-testid={`connect-account-link-${provider}`}
        >
          <Icon />
          <span className="grow">
            Connected: <b>{providerUniqueID}</b>
          </span>
          <CheckIcon className="w-[20px] h-[20px]" />
        </a>
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
    <div class="text-grey-6 text-sm/relaxed" data-testid="connect-your-account">
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
    </div>
  );
}

export default function AccountSettingsForms() {
  const config = useContext(Config) as AccountSettingsConfigObject;

  return (
    <>
      <ChangeEmailForm config={config} />
      <ChangePasswordForm config={config} />
      <ConnectAccountButtons config={config} />
    </>
  );
}
