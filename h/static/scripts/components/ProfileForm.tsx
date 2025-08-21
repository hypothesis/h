import { useContext } from 'preact/hooks';

import { LoginFormsConfig } from '../config';
import type { ProfileConfigObject } from '../config';
import { useFormValue } from '../util/form-value';
import type { FormValue } from '../util/form-value';
import Form from './Form';
import FormFooter from './FormFooter';
import TextField from './TextField';

export default function ProfileForm() {
  const config = useContext(LoginFormsConfig) as ProfileConfigObject;
  const form = config.form;

  const displayName = useFormValue(form, 'display_name', '');
  const description = useFormValue(form, 'description', '');
  const location = useFormValue(form, 'location', '');
  const link = useFormValue(form, 'link', '');
  const orcid = useFormValue(form, 'orcid', '');

  const textFieldProps = (field: FormValue<string>) => ({
    value: field.value,
    fieldError: field.error,
    onChangeValue: field.update,
    onCommitValue: field.commit,
  });

  return (
    <>
      <Form csrfToken={config.csrfToken}>
        <TextField
          name="display_name"
          label="Display name"
          maxLength={30}
          {...textFieldProps(displayName)}
        />
        <TextField
          name="description"
          type="textarea"
          label="Description"
          maxLength={250}
          {...textFieldProps(description)}
        />
        <TextField
          name="location"
          label="Location"
          {...textFieldProps(location)}
        />
        <TextField name="link" label="Link" {...textFieldProps(link)} />
        <TextField
          name="orcid"
          label="ORCID Identifier"
          {...textFieldProps(orcid)}
        />
        <FormFooter />
      </Form>
    </>
  );
}
