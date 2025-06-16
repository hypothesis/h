import { Button } from '@hypothesis/frontend-shared';
import { useContext } from 'preact/hooks';

import Checkbox from '../../forms-common/components/Checkbox';
import FormContainer from '../../forms-common/components/FormContainer';
import TextField from '../../forms-common/components/TextField';
import { useFormValue } from '../../forms-common/form-value';
import { Config } from '../config';
import type { SignupConfigObject } from '../config';

export default function SignupForm() {
  const config = useContext(Config) as SignupConfigObject;

  const username = useFormValue(config.formData?.username ?? '', {
    initialError: config.formErrors?.username,
    validate: username => {
      if (!username.match(/^[A-Za-z0-9_.]*$/)) {
        return 'Must have only letters, numbers, periods and underscores.';
      }
      return undefined;
    },
  });
  const email = useFormValue(config.formData?.email ?? '', {
    initialError: config.formErrors?.email,
  });
  const password = useFormValue(config.formData?.password ?? '', {
    initialError: config.formErrors?.password,
  });
  const privacyAccepted = useFormValue(
    config.formData?.privacy_accepted ?? false,
    {
      initialError: config.formErrors?.privacy_accepted,
    },
  );
  const commsOptIn = useFormValue(config.formData?.comms_opt_in ?? false);

  return (
    <FormContainer>
      <form
        method="POST"
        data-testid="form"
        className="max-w-[530px] mx-auto flex flex-col gap-y-4"
      >
        <input type="hidden" name="csrf_token" value={config.csrfToken} />
        <TextField
          type="input"
          name="username"
          value={username.value}
          fieldError={username.error}
          onChangeValue={username.update}
          label="Username"
          minLength={3}
          maxLength={30}
          autofocus
          required
          showRequired={false}
        />
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
          <a className="link" href="https://web.hypothes.is/terms-of-service/">
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
          <Button type="submit" variant="primary" data-testid="submit-button">
            Sign up
          </Button>
        </div>
      </form>
    </FormContainer>
  );
}
