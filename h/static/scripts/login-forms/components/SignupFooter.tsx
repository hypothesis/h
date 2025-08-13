import { Link } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useContext } from 'preact/hooks';

import { Config } from '../config';
import type { SignupConfigObject } from '../config';

export type SignupFooterProps = {
  /** Action to offer the user in the footer. */
  action: 'login' | 'signup';
};

/**
 * Footer for login and signup forms which gives the user the option to:
 *
 * - Log in if they are on the signup form and they already have an account OR
 * - Sign up if they are on a login form and they don't have an account
 */
export default function SignupFooter({ action }: SignupFooterProps) {
  const config = useContext(Config) as SignupConfigObject;

  return (
    <footer
      className={classnames({
        'fixed bottom-0 left-0 right-0 p-4': config.forOAuth,
        'my-8 py-4': !config.forOAuth,
        'border-t border-t-text-grey-6 text-grey-7': true,
      })}
    >
      {action === 'login' && (
        <>
          Already have an account?{' '}
          <Link
            data-testid="login-link"
            underline="always"
            href={config.urls.login.username_or_email}
            variant="text"
          >
            Log in
          </Link>
        </>
      )}
      {action === 'signup' && (
        <>
          Don{"'"}t have a Hypothesis account?{' '}
          <Link
            data-testid="signup-link"
            underline="always"
            href={config.urls.signup}
            variant="text"
          >
            Sign up
          </Link>
        </>
      )}
    </footer>
  );
}
