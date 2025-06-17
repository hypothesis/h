import { Button } from '@hypothesis/frontend-shared';
import { useContext } from 'preact/hooks';

import FormContainer from '../../forms-common/components/FormContainer';
import TextField from '../../forms-common/components/TextField';
import { useFormValue } from '../../forms-common/form-value';
import { Config } from '../config';
import type { ProfileConfigObject } from '../config';

export default function ProfileForm() {
  const config = useContext(Config) as ProfileConfigObject;

  const displayName = useFormValue(config.formData?.display_name ?? '', {
    initialError: config.formErrors?.display_name,
  });
  const description = useFormValue(config.formData?.description ?? '', {
    initialError: config.formErrors?.description,
  });
  const location = useFormValue(config.formData?.location ?? '', {
    initialError: config.formErrors?.location,
  });
  const link = useFormValue(config.formData?.link ?? '', {
    initialError: config.formErrors?.link,
  });

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
          name="display_name"
          value={displayName.value}
          fieldError={displayName.error}
          onChangeValue={displayName.update}
          label="Display name"
          maxLength={30}
        />
        <TextField
          type="textarea"
          name="description"
          value={description.value}
          fieldError={description.error}
          onChangeValue={description.update}
          label="Description"
          maxLength={250}
        />
        <TextField
          type="input"
          name="location"
          value={location.value}
          fieldError={location.error}
          onChangeValue={location.update}
          label="Location"
        />
        <TextField
          type="input"
          name="link"
          value={link.value}
          fieldError={link.error}
          onChangeValue={link.update}
          label="Link"
        />
        <div className="mb-8 pt-2 flex items-center gap-x-4">
          <div className="grow" />
          <Button type="submit" variant="primary" data-testid="submit-button">
            Save
          </Button>
        </div>
      </form>
    </FormContainer>
  );
}
