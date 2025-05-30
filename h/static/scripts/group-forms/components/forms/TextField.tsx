import { Input, Textarea } from '@hypothesis/frontend-shared';
import { useEffect, useId, useRef, useState } from 'preact/hooks';

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

  /** Current value of the input. */
  value: string;

  /** Callback invoked when the field's value is changed. */
  onChangeValue: (newValue: string) => void;

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

  /** True if the field should be automatically focused on first render. */
  autofocus?: boolean;

  /** Additional classes to apply to the input element. */
  classes?: string;
};

/**
 * A single or multi-line text field with an associated label and optional
 * character limit indicator.
 */
export default function TextField({
  type = 'input',
  value,
  onChangeValue,
  minLength = 0,
  maxLength,
  label,
  required = false,
  autofocus = false,
  classes = '',
}: TextFieldProps) {
  const id = useId();
  const [hasCommitted, setHasCommitted] = useState(false);

  const handleInput = (e: InputEvent) => {
    onChangeValue((e.target as HTMLInputElement).value);
  };

  const handleChange = () => {
    setHasCommitted(true);
  };

  let error = '';
  if (typeof maxLength === 'number' && [...value].length > maxLength) {
    error = `Must be ${maxLength} characters or less.`;
  } else if ([...value].length < minLength && hasCommitted) {
    error = `Must be ${minLength} characters or more.`;
  }

  const InputComponent = type === 'input' ? Input : Textarea;

  // Apply autofocus. We do this ourselves rather than use the input's
  // `autofocus` attribute to work around an issue with autofocus not being
  // applied to elements in Shadow DOM in Safari and Firefox.
  // See https://github.com/hypothesis/h/pull/9596#issuecomment-2922175483.
  const inputRef = useRef<HTMLElement>();
  useEffect(() => {
    if (autofocus) {
      inputRef.current?.focus();
    }
    // This will also trigger if `autofocus` changes after mount. That's OK.
  }, [autofocus]);

  return (
    <div>
      <Label htmlFor={id} text={label} required={required} />
      <InputComponent
        id={id}
        elementRef={inputRef}
        onInput={handleInput}
        onChange={handleChange}
        error={error}
        value={value}
        classes={classes}
        autocomplete="off"
        required={required}
      />
      {typeof maxLength === 'number' && (
        <CharacterCounter
          value={[...value].length}
          limit={maxLength}
          error={Boolean(error)}
        />
      )}
    </div>
  );
}
