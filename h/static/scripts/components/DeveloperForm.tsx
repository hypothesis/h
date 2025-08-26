import { Callout, Link, InputGroup, Input } from '@hypothesis/frontend-shared';
import { useContext, useId } from 'preact/hooks';

import { LoginFormsConfig } from '../config';
import type { DeveloperConfigObject } from '../config';
import AccountFormHeader from './AccountFormHeader';
import CopyButton from './CopyButton';
import Form from './Form';
import FormFooter from './FormFooter';
import Label from './Label';
import Text from './Text';

export default function DeveloperForm() {
  const config = useContext(LoginFormsConfig) as DeveloperConfigObject;
  const token = config.token;

  const inputId = useId();

  return (
    <>
      <AccountFormHeader />
      <Text>
        API tokens can be used to access your data via the{' '}
        <Link
          target="_blank"
          href="https://h.readthedocs.io/en/latest/api/"
          underline="always"
        >
          Hypothesis API
        </Link>
        .
      </Text>
      <Callout status="notice" classes="my-4">
        <b>Keep your API tokens safe</b> as they can be used to access all data
        in your account.
      </Callout>
      <Form classes="mt-8" csrfToken={config.csrfToken}>
        {token && (
          <>
            <Label htmlFor={inputId} text="Current API token" />
            <InputGroup>
              <Input
                id={inputId}
                name="token"
                readonly
                value={token}
                // Use monospace font for better legibility.
                classes="font-mono"
              />
              <CopyButton title="Copy token" value={token} />
            </InputGroup>
          </>
        )}
        <FormFooter
          submitLabel={token ? 'Recreate API token' : 'Create API token'}
        />
      </Form>
    </>
  );
}
