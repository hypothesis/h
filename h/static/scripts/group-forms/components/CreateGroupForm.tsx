import { useEffect, useId, useMemo, useState } from 'preact/hooks';

import { Button, Input, Spinner, Textarea } from '@hypothesis/frontend-shared';
import { readConfig } from '../config';
import { callAPI, CreateGroupAPIResponse } from '../utils/api';
import { setLocation } from '../utils/set-location';

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
      {required && <Star />}
    </label>
  );
}

function TextField({
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
}: {
  type: 'input' | 'textarea';
  value: string;
  onChangeValue: (newValue: string) => void;
  minLength?: number;
  maxLength: number;
  label: string;
  testid: string;
  required?: boolean;
  autofocus?: boolean;
  classes?: string;
}) {
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

export default function CreateGroupForm() {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [saving, setSaving] = useState(false);
  const config = useMemo(() => readConfig(), []);

  useEffect(() => {
    const listener = (e: PageTransitionEvent) => {
      if (e.persisted) {
        // Disable the "saving" state if the user uses the browser's Back button to navigate
        // back to the group form.
        setSaving(false);
      }
    };
    window.addEventListener('pageshow', listener);
    return () => window.removeEventListener('pageshow', listener);
  }, []);

  const createGroup = async (e: SubmitEvent) => {
    e.preventDefault();

    let response: CreateGroupAPIResponse;

    setSaving(true);

    try {
      response = (await callAPI(
        config.api.createGroup.url,
        config.api.createGroup.method,
        {
          name,
          description,
        },
      )) as CreateGroupAPIResponse;
    } catch (apiError) {
      setErrorMessage(apiError.message);
      setSaving(false);
      return;
    }

    setLocation(response.links.html);
  };

  return (
    <div className="text-grey-6 text-sm/relaxed">
      <h1 className="mt-14 mb-8 text-grey-7 text-xl/none">
        Create a new private group
      </h1>

      <form onSubmit={createGroup} data-testid="form">
        <TextField
          type="input"
          value={name}
          onChangeValue={setName}
          minLength={3}
          maxLength={25}
          label="Name"
          testid="name"
          autofocus
          required
        />
        <TextField
          type="textarea"
          value={description}
          onChangeValue={setDescription}
          maxLength={250}
          label="Description"
          testid="description"
          classes="h-24"
        />

        <div className="flex items-center gap-x-4">
          {errorMessage && (
            <div
              className="text-red-error font-bold"
              data-testid="error-message"
            >
              {errorMessage}
            </div>
          )}
          <div className="grow" />
          {saving && <Spinner data-testid="spinner" />}
          <Button
            type="submit"
            variant="primary"
            disabled={saving}
            data-testid="button"
          >
            Create group
          </Button>
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
