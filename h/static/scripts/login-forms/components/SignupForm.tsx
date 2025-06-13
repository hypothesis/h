import { Button } from '@hypothesis/frontend-shared';
import { useContext, useState } from 'preact/hooks';

import Checkbox from '../../forms-common/components/Checkbox';
import FormContainer from '../../forms-common/components/FormContainer';
import TextField from '../../forms-common/components/TextField';
import { Config } from '../config';

export default function SignupForm() {
  const config = useContext(Config)!;

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
          label="Username / email"
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
          onChange={e => {
            setPrivacyAccepted((e.target as HTMLInputElement).checked);
          }}
          error={config.formErrors?.privacy_accepted ?? ''}
          required
        >
          <PrivacyAcceptedMessage />
        </Checkbox>
        <input
          type="hidden"
          name="privacy_accepted"
          value={privacyAccepted.toString()}
        />
        <Checkbox
          data-testid="comms-opt-in"
          checked={commsOptIn}
          onChange={e => {
            setCommsOptIn((e.target as HTMLInputElement).checked);
          }}
        >
          I would like to receive news about annotation and Hypothesis.
        </Checkbox>
        <input
          type="hidden"
          name="comms_opt_in"
          value={commsOptIn.toString()}
        />
        <div className="mb-8 pt-2 flex items-center gap-x-4">
          <div className="grow" />
          <Button type="submit" variant="primary" data-testid="submit-button">
            Sign up
          </Button>
        </div>
      </form>
    </FormContainer>
  );
}

function PrivacyAcceptedMessage() {
  return (
    <>
      I have read and agree to the{' '}
      <a className="link" href="https://web.hypothes.is/privacy/">
        privacy policy
      </a>
      ,{' '}
      <a className="link" href="https://web.hypothes.is/terms-of-service/">
        terms of service
      </a>
      , and{' '}
      <a className="link" href="https://web.hypothes.is/community-guidelines/">
        community guidelines
      </a>
      .
    </>
  );
}
