import { useContext } from 'preact/hooks';

import { LoginFormsConfig } from '../config';
import type { ForgotPasswordConfigObject } from '../config';
import { useFormValue } from '../util/form-value';
import Form from './Form';
import FormFooter from './FormFooter';
import FormHeader from './FormHeader';
import Text from './Text';
import TextField from './TextField';

export default function ForgotPasswordForm() {
  const config = useContext(LoginFormsConfig) as ForgotPasswordConfigObject;
  const form = config.form;

  const email = useFormValue(form, 'email', '');

  return (
    <>
      <FormHeader>Reset your password</FormHeader>
      <div
        // The max width here and item gap should match SignupSelectForm.
        //
        // This keeps the positioning of items consistent if the user navigates
        // from the login page to this page.
        className="mx-auto max-w-[400px] flex flex-col gap-y-3 items-stretch"
      >
        <Text>
          Enter your email address and a password reset link will be sent to
          you.
        </Text>
        <Form
          csrfToken={config.csrfToken}
          // Remove `mx-auto` from this form since it is applied to the parent.
          center={false}
        >
          <TextField
            type="input"
            inputType="email"
            name="email"
            value={email.value}
            fieldError={email.error}
            onChangeValue={email.update}
            label="Email address"
            autofocus
            required
            showRequired={false}
          />
          <FormFooter submitLabel="Send password reset link" />
        </Form>
      </div>
    </>
  );
}
