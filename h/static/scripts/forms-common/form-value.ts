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
   */
  validate?: (value: T) => string | undefined;

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

  /** Update the form value. This will change {@link FormValue.changed} to `true`. */
  update: (value: T) => void;

  /** True if the value has been changed via {@link FormValue.update} since it was last submitted. */
  changed: boolean;

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
  const update = useCallback((value: T) => {
    setValue(value);
    setChanged(true);
  }, []);

  let error;
  if (changed) {
    error = opts.validate?.(value);
  } else {
    error = opts.initialError;
  }
  return { value, update, changed, error };
}
