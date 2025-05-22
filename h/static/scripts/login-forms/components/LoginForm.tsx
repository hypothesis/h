import { Button } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
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
        method="POST"
        data-testid="form"
        className={classnames({
          'max-w-[530px] mx-auto flex flex-col': true,
          'gap-y-4': !config.forOAuth,
          // Use a more compact layout in the OAuth popup window.
          'gap-y-2': config.forOAuth,
        })}
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
          {config.forOAuth && (
            <Button
              type="button"
              variant="secondary"
              data-testid="cancel-button"
              onClick={() => window.close()}
            >
              Cancel
            </Button>
          )}
          <div className="grow" />
          <Button type="submit" variant="primary" data-testid="submit-button">
            Log in
          </Button>
        </div>
      </form>
    </FormContainer>
  );
}
