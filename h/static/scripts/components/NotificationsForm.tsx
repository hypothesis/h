import { Callout, Link } from '@hypothesis/frontend-shared';
import { useContext } from 'preact/hooks';

import { LoginFormsConfig } from '../config';
import type { NotificationsConfigObject } from '../config';
import { routes } from '../routes';
import { useFormValue } from '../util/form-value';
import type { FormValue } from '../util/form-value';
import Checkbox from './Checkbox';
import Form from './Form';
import FormFooter from './FormFooter';

export default function NotificationsForm() {
  const config = useContext(LoginFormsConfig) as NotificationsConfigObject;

  const form = config.form;
  const reply = useFormValue(form, 'reply', true);
  const mention = useFormValue(form, 'mention', true);
  const moderation = useFormValue(form, 'moderation', true);

  const checkboxProps = (field: FormValue<boolean>) => {
    return {
      name: field.name,
      checked: field.value,
      // Backend form validation expects the string "true" rather than the
      // HTML form default of "on".
      value: 'true',
      onChange: (e: Event) => {
        field.update((e.target as HTMLInputElement).checked);
      },
    };
  };

  if (!config.hasEmail) {
    return (
      <Callout>
        Notifications will not be sent because your account does not have an
        email address. You can add an email address in{' '}
        <Link underline="always" href={routes.accountSettings}>
          account settings
        </Link>
        .
      </Callout>
    );
  }

  return (
    <Form csrfToken={config.csrfToken}>
      <p>Email me when someone:</p>
      <Checkbox data-testid="reply-checkbox" {...checkboxProps(reply)}>
        Replies to my annotations
      </Checkbox>
      <Checkbox data-testid="mention-checkbox" {...checkboxProps(mention)}>
        Mentions me in an annotation
      </Checkbox>
      <Checkbox
        data-testid="moderation-checkbox"
        {...checkboxProps(moderation)}
      >
        Moderates my annotations
      </Checkbox>
      <FormFooter />
    </Form>
  );
}
