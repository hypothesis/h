import { useId, useState } from 'preact/hooks';
import { Input, Textarea } from '@hypothesis/frontend-shared';

import Label from './Label';
import Star from './Star';

function CharacterCounter({
  value,
  limit,
  testid,
  error = false,
}: {
  value: number;
  limit: number;
  testid: string;
  error?: boolean;
}) {
  return (
    <div className="flex">
      <div className="grow" />
      <span
        data-testid={testid}
        className={error ? 'text-red-error font-bold' : undefined}
      >
        {value}/{limit}
      </span>
    </div>
  );
}

export type TextFieldProps = {
  /** The DOM element to render. */
  type: 'input' | 'textarea';

  /** Current value of the input. */
  value: string;
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
  maxLength: number;

  /** Text for the label shown next to the field. */
  label: string;

  testid: string;
  required?: boolean;
  autofocus?: boolean;
  classes?: string;
};

/**
 * A single or multi-line text field with an associated label and optional
 * character limit indicator.
 */
export default function TextField({
  type,
  value,
  onChangeValue,
  minLength = 0,
  maxLength,
  label,
  testid,
  required = false,
  autofocus = false,
  classes = '',
}: TextFieldProps) {
  const id = useId();
  const [hasCommitted, setHasCommitted] = useState(false);

  const handleInput = (e: InputEvent) => {
    onChangeValue((e.target as HTMLInputElement).value);
  };

  const handleChange = (e: Event) => {
    setHasCommitted(true);
  };

  let error = '';
  if ([...value].length > maxLength) {
    error = `Must be ${maxLength} characters or less.`;
  } else if ([...value].length < minLength && hasCommitted) {
    error = `Must be ${minLength} characters or more.`;
  }

  const InputComponent = type === 'input' ? Input : Textarea;

  return (
    <div className="mb-4">
      <Label htmlFor={id} text={label} required={required} />
      <InputComponent
        id={id}
        onInput={handleInput}
        onChange={handleChange}
        error={error}
        value={value}
        classes={classes}
        autofocus={autofocus}
        autocomplete="off"
        required={required}
        data-testid={testid}
      />
      <CharacterCounter
        value={[...value].length}
        limit={maxLength}
        testid={`charcounter-${testid}`}
        error={Boolean(error)}
      />
    </div>
  );
}
