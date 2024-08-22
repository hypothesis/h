import { useEffect, useId, useMemo, useState } from 'preact/hooks';

import {
  Button,
  CancelIcon,
  Input,
  Textarea,
} from '@hypothesis/frontend-shared';
import { readConfig } from '../config';
import { callAPI, CreateUpdateGroupAPIResponse } from '../utils/api';
import { setLocation } from '../utils/set-location';
import SaveStateIcon from './SaveStateIcon';

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

export default function CreateEditGroupForm() {
  const config = useMemo(() => readConfig(), []);
  const group = config.context.group;

  const [name, setName] = useState(group?.name ?? '');
  const [description, setDescription] = useState(group?.description ?? '');
  const [errorMessage, setErrorMessage] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const listener = (e: PageTransitionEvent) => {
      if (e.persisted) {
        // Disable the "saving" state if the user uses the browser's Back button to navigate
        // back to the group form.
        setSaving(false);
        setSaved(false);
      }
    };
    window.addEventListener('pageshow', listener);
    return () => window.removeEventListener('pageshow', listener);
  }, []);

  const handleChangeName = (newName: string) => {
    setName(newName);
    setSaved(false);
  };

  const handleChangeDescription = (newDescription: string) => {
    setDescription(newDescription);
    setSaved(false);
  };

  const createGroup = async (e: SubmitEvent) => {
    e.preventDefault();
    setErrorMessage('');

    let response: CreateUpdateGroupAPIResponse;

    setSaving(true);

    try {
      response = (await callAPI(config.api.createGroup.url, {
        method: config.api.createGroup.method,
        headers: config.api.createGroup.headers,
        json: {
          name,
          description,
        },
      })) as CreateUpdateGroupAPIResponse;
    } catch (apiError) {
      setErrorMessage(apiError.message);
      setSaving(false);
      return;
    }

    setLocation(response.links.html);
  };

  const updateGroup = async (e: SubmitEvent) => {
    e.preventDefault();
    setErrorMessage('');
    setSaved(false);
    setSaving(true);

    let response: CreateUpdateGroupAPIResponse;

    try {
      response = (await callAPI(config.api.updateGroup!.url, {
        method: config.api.updateGroup!.method,
        headers: config.api.updateGroup!.headers,
        json: { id: group!.pubid, name, description },
      })) as CreateUpdateGroupAPIResponse;
    } catch (apiError) {
      setErrorMessage(apiError.message);
      return;
    } finally {
      setSaving(false);
    }

    setSaved(true);
  };

  let onSubmit;
  if (group) {
    onSubmit = updateGroup;
  } else {
    onSubmit = createGroup;
  }

  return (
    <div className="text-grey-6 text-sm/relaxed">
      <h1 className="mt-14 mb-8 text-grey-7 text-xl/none" data-testid="header">
        {group ? 'Edit group' : 'Create a new private group'}
      </h1>

      <form onSubmit={onSubmit} data-testid="form">
        <TextField
          type="input"
          value={name}
          onChangeValue={handleChangeName}
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
          onChangeValue={handleChangeDescription}
          maxLength={250}
          label="Description"
          testid="description"
          classes="h-24"
        />

        <div className="flex items-center gap-x-4">
          {errorMessage && (
            <div
              className="text-red-error font-bold flex items-center gap-x-2"
              data-testid="error-message"
            >
              <CancelIcon />
              {errorMessage}
            </div>
          )}
          <div className="grow" />
          <SaveStateIcon
            state={saving ? 'saving' : saved ? 'saved' : 'unsaved'}
          />
          <Button
            type="submit"
            variant="primary"
            disabled={saving}
            data-testid="button"
          >
            {group ? 'Save changes' : 'Create group'}
          </Button>
        </div>
      </form>

      <footer className="mt-14 pt-4 border-t border-t-text-grey-6">
        <div className="flex">
          {group && (
            <a href={group.link} data-testid="back-link">
              ← Back to group overview page
            </a>
          )}
          <div className="grow" />
          <Star />
          &nbsp;Required
        </div>
      </footer>
    </div>
  );
}
