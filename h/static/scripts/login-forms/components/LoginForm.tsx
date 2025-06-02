import { Button } from '@hypothesis/frontend-shared';
import { useContext, useState } from 'preact/hooks';

import FormContainer from '../../forms-common/components/FormContainer';
import TextField from '../../forms-common/components/TextField';
import { Config } from '../config';
import { routes } from '../routes';

export default function LoginForm() {
  const config = useContext(Config)!;

  const [username, setUsername] = useState(config.formData?.username ?? '');
  const [password, setPassword] = useState(config.formData?.password ?? '');

  return (
    <FormContainer>
      <form
        action={routes.login}
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
          autofocus
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
          required
          showRequired={false}
        />
        <div className="text-right">
          <a
            href={routes.forgotPassword}
            className="text-grey-5 text-sm underline"
            data-testid="forgot-password-link"
          >
            Forgot your password?
          </a>
        </div>
        <div className="mb-8 pt-2 flex items-center gap-x-4">
          <div className="grow" />
          <Button type="submit" variant="primary" data-testid="button">
            Log in
          </Button>
        </div>
      </form>
    </FormContainer>
  );
}
