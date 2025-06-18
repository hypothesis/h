import { Button, Link } from '@hypothesis/frontend-shared';
import { useContext } from 'preact/hooks';

import Form from '../../forms-common/components/Form';
import FormContainer from '../../forms-common/components/FormContainer';
import TextField from '../../forms-common/components/TextField';
import { useFormValue } from '../../forms-common/form-value';
import { Config } from '../config';
import type { LoginConfigObject } from '../config';
import { routes } from '../routes';

export default function LoginForm() {
  const config = useContext(Config) as LoginConfigObject;

  const username = useFormValue(config.formData?.username ?? '', {
    initialError: config.formErrors?.username,
  });
  const password = useFormValue(config.formData?.password ?? '', {
    initialError: config.formErrors?.password,
  });

  return (
    <FormContainer>
      <Form csrfToken={config.csrfToken}>
        <TextField
          type="input"
          name="username"
          value={username.value}
          fieldError={username.error}
          onChangeValue={username.update}
          label="Username / email"
          autofocus
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
          required
          showRequired={false}
        />
        <div className="text-right">
          <Link
            href={routes.forgotPassword}
            underline="always"
            variant="text-light"
            data-testid="forgot-password-link"
          >
            Forgot your password?
          </Link>
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
      </Form>
    </FormContainer>
  );
}
