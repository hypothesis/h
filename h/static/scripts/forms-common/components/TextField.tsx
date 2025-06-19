import { Input, Textarea } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useId, useState } from 'preact/hooks';

import ErrorNotice from './ErrorNotice';
import Label from './Label';

function CharacterCounter({
  value,
  limit,
  error = false,
}: {
  value: number;
  limit: number;
  error?: boolean;
}) {
  return (
    <div className="flex">
      <div className="grow" />
      <span
        data-testid="char-counter"
        className={error ? 'text-red-error font-bold' : undefined}
      >
        {value}/{limit}
      </span>
    </div>
  );
}

export type TextFieldProps = {
  /** The DOM element to render. */
  type?: 'input' | 'textarea';

  /** The type of input element, e.g., "text", "password", etc. */
  inputType?: 'text' | 'password';

  /** Name of the input field. */
  name?: string;

  /** Current value of the input. */
  value: string;

  /** Callback invoked when the field's value is changed. */
  onChangeValue: (newValue: string) => void;

  /** Callback invoked when the field's value is committed. */
  onCommitValue?: (newValue: string) => void;

  /**
   * Minimum number of characters that this field must have.
   *
   * This is a count of Unicode code points, not UTF-16 code units.
   */
  minLength?: number;

  /**
   * Maximum number of characters that may be entered.
   *
   * This is a count of Unicode code points, not UTF-16 code units.
   */
  maxLength?: number;

  /** Text for the label shown next to the field. */
  label: string;

  /** True if this is a required field. */
  required?: boolean;

  /** True if the required indicator should be shown next to the label. */
  showRequired?: boolean;

  /** True if the field should be automatically focused on first render. */
  autofocus?: boolean;

  /** Additional classes to apply to the input element. */
  classes?: string;

  /** Optional error message for the field. */
  fieldError?: string;

  /**
   * Whether the status line, containing the character count, affects the layout
   * size.
   *
   * This defaults to false, so that fields in a vertical layout have the same
   * vertical spacing if some fields have a status line and some do not.
   */
  includeStatusLineInLayout?: boolean;
};

/**
 * A single or multi-line text field with an associated label and optional
 * character limit indicator.
 */
export default function TextField({
  type = 'input',
  inputType,
  value,
  onChangeValue,
  onCommitValue,
  minLength = 0,
  maxLength,
  label,
  required = false,
  showRequired = required,
  autofocus = false,
  classes = '',
  name,
  fieldError = '',
  includeStatusLineInLayout = false,
}: TextFieldProps) {
  const id = useId();
  const [hasCommitted, setHasCommitted] = useState(false);

  let error = '';
  if (typeof maxLength === 'number' && [...value].length > maxLength) {
    error = `Must be ${maxLength} characters or less.`;
  } else if ([...value].length < minLength && hasCommitted) {
    error = `Must be ${minLength} characters or more.`;
  }

  const InputComponent = type === 'input' ? Input : Textarea;

  return (
    <div className="relative">
      <Label htmlFor={id} text={label} required={showRequired} />
      <InputComponent
        id={id}
        onInput={e => {
          onChangeValue((e.target as HTMLInputElement).value);
        }}
        onChange={e => {
          onCommitValue?.((e.target as HTMLInputElement).value);
          setHasCommitted(true);
        }}
        error={error}
        value={value}
        classes={classes}
        autofocus={autofocus}
        autocomplete="off"
        required={required}
        name={name}
        type={inputType}
      />
      <div
        className={classnames(
          includeStatusLineInLayout ? 'relative' : 'absolute',
          'w-full',
        )}
        data-testid="status-line"
      >
        {typeof maxLength === 'number' && (
          <CharacterCounter
            value={[...value].length}
            limit={maxLength}
            error={Boolean(error)}
          />
        )}
      </div>
      {fieldError && (
        <div className="mt-1">
          <ErrorNotice message={fieldError} />
        </div>
      )}
    </div>
  );
}
