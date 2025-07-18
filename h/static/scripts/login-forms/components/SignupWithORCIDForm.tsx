import { Button } from '@hypothesis/frontend-shared';
import { useContext, useEffect, useState } from 'preact/hooks';

import Checkbox from '../../forms-common/components/Checkbox';
import Form from '../../forms-common/components/Form';
import FormContainer from '../../forms-common/components/FormContainer';
import TextField from '../../forms-common/components/TextField';
import { useFormValue } from '../../forms-common/form-value';
import { Config } from '../config';
import type { SignupWithORCIDConfigObject } from '../config';

export default function SignupWithORCIDForm() {
  const config = useContext(Config) as SignupWithORCIDConfigObject;
  const orcidId = config.identity.orcid.id;
  const [idInfoJWT, setIDInfoJWT] = useState<string>();

  const username = useFormValue(config.formData?.username ?? '', {
    initialError: config.formErrors?.username,
    validate: (username, committed) => {
      if (!username.match(/^[A-Za-z0-9_.]*$/)) {
        return 'Must have only letters, numbers, periods and underscores.';
      }
      if (committed && (username.startsWith('.') || username.endsWith('.'))) {
        return 'May not start or end with a period.';
      }
      return undefined;
    },
  });

  const privacyAccepted = useFormValue(
    config.formData?.privacy_accepted ?? false,
    {
      initialError: config.formErrors?.privacy_accepted,
    },
  );

  const commsOptIn = useFormValue(config.formData?.comms_opt_in ?? false);
  const idinfo = config.formData?.idinfo;

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const idInfoQueryParam = urlParams.get('idinfo');

    if (idInfoQueryParam) {
      setIDInfoJWT(idInfoQueryParam);

      urlParams.delete('idinfo');
      const newUrl =
        window.location.pathname +
        (urlParams.toString() ? '?' + urlParams.toString() : '') +
        window.location.hash;
      window.history.replaceState({}, '', newUrl);
    } else {
      setIDInfoJWT(idinfo);
    }
  }, [idinfo]);

  return (
    <FormContainer>
      <p>
        Connected: <b>{orcidId}</b>
      </p>
      <Form csrfToken={config.csrfToken}>
        <input type="hidden" name="idinfo" value={idInfoJWT} />
        <TextField
          type="input"
          name="username"
          value={username.value}
          fieldError={username.error}
          onChangeValue={username.update}
          onCommitValue={username.commit}
          label="Username"
          minLength={3}
          maxLength={30}
          autofocus
          required
          showRequired={false}
        />
        <Checkbox
          data-testid="privacy-accepted"
          checked={privacyAccepted.value}
          name="privacy_accepted"
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
      </Form>
    </FormContainer>
  );
}
