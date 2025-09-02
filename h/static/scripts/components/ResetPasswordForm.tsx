import { useContext } from 'preact/hooks';

import { LoginFormsConfig } from '../config';
import type { ResetPasswordConfigObject } from '../config';
import { useFormValue } from '../util/form-value';
import Form from './Form';
import FormFooter from './FormFooter';
import FormHeader from './FormHeader';
import Text from './Text';
import TextField from './TextField';

export default function ResetPasswordForm() {
  const config = useContext(LoginFormsConfig) as ResetPasswordConfigObject;
  const form = config.form;

  const hasCode = Boolean(form.data?.user);

  // TODO - Hide form field if config contains a code.
  const resetCode = useFormValue(form, 'user', '');
  const password = useFormValue(form, 'password', '');

  return (
    <>
      <FormHeader>Choose new password</FormHeader>
      <div
        // The max width here and item gap should match SignupSelectForm.
        //
        // This keeps the positioning of items consistent if the user navigates
        // from the login page to this page.
        className="mx-auto max-w-[400px] flex flex-col gap-y-3 items-stretch"
      >
        {!hasCode && (
          <Text>
            Enter the reset code that was emailed to you to change the password
            for your account.
          </Text>
        )}
        <Form
          csrfToken={config.csrfToken}
          // Remove `mx-auto` from this form since it is applied to the parent.
          center={false}
        >
          {hasCode ? (
            <input type="hidden" name="user" value={resetCode.value} />
          ) : (
            <TextField
              type="input"
              name="user"
              value={resetCode.value}
              fieldError={resetCode.error}
              onChangeValue={resetCode.update}
              label="Reset code"
              autofocus
              required
              showRequired={false}
            />
          )}
          <TextField
            type="input"
            inputType="password"
            name="password"
            value={password.value}
            fieldError={password.error}
            onChangeValue={password.update}
            label="New password"
            autofocus
            required
            showRequired={false}
          />
          <FormFooter submitLabel="Reset password" />
        </Form>
      </div>
    </>
  );
}
