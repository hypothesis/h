import classnames from 'classnames';
import type { ComponentChildren } from 'preact';
import type { JSX } from 'preact';

export type FormProps = JSX.FormHTMLAttributes & {
  /**
   * CSRF token to render in a hidden field.
   *
   * If the form is not going to be submitted to the backend directly, for
   * example because the frontend is going to make API requests instead, this
   * can be set to `null`. This prop is required so that callers have to make
   * an explicit choice.
   */
  csrfToken: string | null;

  /** Center form in parent container. Defaults to true. */
  center?: boolean;

  /** Additional CSS classes for the form element. */
  classes?: string;

  children: ComponentChildren;
};

/**
 * Wrapper around an HTML form which adds standard styling, CSRF token etc.
 */
export default function Form({
  center = true,
  classes,
  children,
  csrfToken,
  ...formAttrs
}: FormProps) {
  return (
    <form
      method="POST"
      data-testid="form"
      className={classnames(
        'max-w-[530px] flex flex-col gap-y-4',
        center && 'mx-auto',
        classes,
      )}
      {...formAttrs}
    >
      {csrfToken && <input type="hidden" name="csrf_token" value={csrfToken} />}
      {children}
    </form>
  );
}
