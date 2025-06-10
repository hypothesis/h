import { Button } from '@hypothesis/frontend-shared';
import { useContext, useState } from 'preact/hooks';

import Checkbox from '../../forms-common/components/Checkbox';
import FormContainer from '../../forms-common/components/FormContainer';
import TextField from '../../forms-common/components/TextField';
import { Config } from '../config';
import type { SignupConfigObject } from '../config';

export default function SignupForm() {
  const config = useContext(Config) as SignupConfigObject;

  const [username, setUsername] = useState(config.formData?.username ?? '');
  const [email, setEmail] = useState(config.formData?.email ?? '');
  const [password, setPassword] = useState(config.formData?.password ?? '');
  const [privacyAccepted, setPrivacyAccepted] = useState(
    config.formData?.privacy_accepted ?? false,
  );
  const [commsOptIn, setCommsOptIn] = useState(
    config.formData?.comms_opt_in ?? false,
  );

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
          value={username}
          fieldError={config.formErrors?.username ?? ''}
          onChangeValue={setUsername}
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
          value={email}
          fieldError={config.formErrors?.email ?? ''}
          onChangeValue={setEmail}
          label="Email address"
          required
          showRequired={false}
        />
        <TextField
          type="input"
          inputType="password"
          name="password"
          value={password}
          fieldError={config.formErrors?.password ?? ''}
          onChangeValue={setPassword}
          label="Password"
          minLength={8}
          required
          showRequired={false}
        />
        <Checkbox
          data-testid="privacy-accepted"
          checked={privacyAccepted}
          name="privacy_accepted"
          // Backend form validation expects the string "true" rather than the
          // HTML form default of "on".
          value="true"
          onChange={e => {
            setPrivacyAccepted((e.target as HTMLInputElement).checked);
          }}
          error={config.formErrors?.privacy_accepted ?? ''}
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
          checked={commsOptIn}
          name="comms_opt_in"
          // Backend form validation expects the string "true" rather than the
          // HTML form default of "on".
          value="true"
          onChange={e => {
            setCommsOptIn((e.target as HTMLInputElement).checked);
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
