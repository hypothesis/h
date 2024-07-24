import { useId, useState } from 'preact/hooks';

import { Button, Input, Textarea } from '@hypothesis/frontend-shared';

function Star() {
  return <span className="text-brand">*</span>;
}

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

function Label({
  htmlFor,
  text,
  required,
}: {
  htmlFor: string;
  text: string;
  required?: boolean;
}) {
  return (
    <label htmlFor={htmlFor}>
      {text}
      {required ? <Star /> : null}
    </label>
  );
}

function TextField({
  type,
  limit,
  label,
  testid,
  required = false,
  autofocus = false,
  classes = '',
}: {
  type: 'input' | 'textarea';
  limit: number;
  label: string;
  testid: string;
  required?: boolean;
  autofocus?: boolean;
  classes?: string;
}) {
  const id = useId();
  const [value, setValue] = useState('');

  const handleInput = (e: InputEvent) => {
    setValue((e.target as HTMLInputElement).value);
  };

  const error = value.length > limit;

  const InputComponent = type === 'input' ? Input : Textarea;

  return (
    <div className="mb-4">
      <Label htmlFor={id} text={label} required={required} />
      <InputComponent
        id={id}
        onInput={handleInput}
        error={error ? `Must be ${limit} characters or less.` : undefined}
        value={value}
        classes={classes}
        autofocus={autofocus}
        autocomplete="off"
        data-testid={testid}
      />
      <CharacterCounter
        value={value.length}
        limit={limit}
        testid={`charcounter-${testid}`}
        error={error}
      />
    </div>
  );
}

export default function CreateGroupForm() {
  return (
    <div className="text-grey-6 text-sm/relaxed">
      <h1 className="mt-14 mb-8 text-grey-7 text-xl/none">
        Create a new private group
      </h1>

      <form>
        <TextField
          type="input"
          limit={25}
          label="Name"
          testid="name"
          autofocus
          required
        />
        <TextField
          type="textarea"
          limit={250}
          label="Description"
          testid="description"
          classes="h-24"
        />

        <div className="flex">
          <div className="grow" />
          <Button variant="primary">Create group</Button>
        </div>
      </form>

      <footer className="mt-14 pt-4 border-t border-t-text-grey-6">
        <div className="flex">
          <div className="grow" />
          <Star />
          &nbsp;Required
        </div>
      </footer>
    </div>
  );
}
