import { useState, useCallback } from 'preact/hooks';

export type FormValueOptions<T> = {
  /**
   * Validate a form value. The callback returns undefined if the form is
   * valid or an error otherwise.
   *
   * If the value is invalid, this will be reflected in {@link FormValue.error}.
   * Whether validation succeeds or fails, {@link FormValue.value} will be updated.
   *
   * The purpose of client-side validation is to notify a user sooner about
   * invalid form values. The server must always perform its own validation,
   * and client-side validation may be a subset of what the server checks.
   *
   * @param value - The new field value
   * @param committed - True if the new value has been committed (ie. when the
   *   user signals they have finished editing the field).
   */
  validate?: (value: T, committed: boolean) => string | undefined;

  /**
   * The error from when the form was last submitted.
   *
   * This is used if the form value has not been changed since it was submitted.
   */
  initialError?: string;
};

export type FormValue<T> = {
  /** Current form field value. */
  value: T;

  /**
   * Update the form value to reflect a pending change.
   *
   * This should be invoked in response to `input` events on the field, when
   * the user is still editing the value.
   *
   * This will change {@link FormValue.changed} to `true`.
   */
  update: (value: T) => void;

  /**
   * Update the form value to reflect a committed change.
   *
   * This should be invoked in response to `change` events on the field, when
   * the user has completed editing the value.
   *
   * This will change {@link FormValue.changed} to `true`.
   */
  commit: (value: T) => void;

  /** True if the value has been changed since it was last submitted. */
  changed: boolean;

  /**
   * True if the value has been committed.
   *
   * A value is _committed_ when the `change` event fires.
   * See https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/change_event.
   */
  committed: boolean;

  /** Current validation error. */
  error?: string;
};

/**
 * Utility to manage the state for a form field value.
 *
 * This keeps track of:
 *
 *  - The current value
 *  - Whether the value has changed since the form was last submitted
 *  - The validation error for the field, which may come from a submission, or
 *    local validation.
 */
export function useFormValue<T>(
  initial: T,
  opts: FormValueOptions<T> = {},
): FormValue<T> {
  const [value, setValue] = useState(initial);
  const [changed, setChanged] = useState(false);
  const [committed, setCommitted] = useState(true);

  const update = useCallback((value: T) => {
    setValue(value);
    setCommitted(false);
    setChanged(true);
  }, []);

  const commit = useCallback((value: T) => {
    setValue(value);
    setCommitted(true);
    setChanged(true);
  }, []);

  let error;
  if (changed) {
    error = opts.validate?.(value, committed);
  } else {
    error = opts.initialError;
  }

  return { value, update, commit, changed, committed, error };
}
