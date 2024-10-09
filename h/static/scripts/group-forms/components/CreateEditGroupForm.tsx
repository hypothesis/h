import { useEffect, useId, useMemo, useState } from 'preact/hooks';

import {
  Button,
  CancelIcon,
  Input,
  RadioGroup,
  Textarea,
  ModalDialog,
  useWarnOnPageUnload,
} from '@hypothesis/frontend-shared';
import { readConfig } from '../config';
import { callAPI } from '../utils/api';
import type {
  CreateUpdateGroupAPIRequest,
  CreateUpdateGroupAPIResponse,
  GroupType,
} from '../utils/api';
import { pluralize } from '../utils/pluralize';
import { setLocation } from '../utils/set-location';
import SaveStateIcon from './SaveStateIcon';
import WarningDialog from './WarningDialog';

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
  id,
  htmlFor,
  text,
  required,
}: {
  id?: string;
  htmlFor?: string;
  text: string;
  required?: boolean;
}) {
  return (
    <label className="font-bold" id={id} htmlFor={htmlFor}>
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

/**
 * Dialog that warns users about existing annotations in a group being exposed
 * or hidden from public view when the group type is changed.
 */
function GroupTypeChangeWarning({
  name,
  newType,
  annotationCount: count,
  onConfirm,
  onCancel,
}: {
  /** Name of the group. */
  name: string;

  /**
   * The new type for the group. If this is private, the old type is inferred
   * to be public and vice-versa.
   */
  newType: GroupType;

  /** Number of annotations in the group. */
  annotationCount: number;

  onConfirm: () => void;
  onCancel: () => void;
}) {
  const newTypeIsPrivate = newType === 'private';

  let title;
  let confirmAction;
  let message;
  if (newTypeIsPrivate) {
    title = `Make ${count} ${pluralize(count, 'annotation', 'annotations')} private?`;
    confirmAction = 'Make annotations private';
    message = `Are you sure you want to make "${name}" a private group? ${count} ${pluralize(count, 'annotation that is', 'annotations that are')} publicly visible will become visible only to members of "${name}".`;
  } else {
    let groupDescription = 'a public group';
    switch (newType) {
      case 'open':
        groupDescription = 'an open group';
        break;
      case 'restricted':
        groupDescription = 'a restricted group';
        break;
    }

    title = `Make ${count} ${pluralize(count, 'annotation', 'annotations')} public?`;
    confirmAction = 'Make annotations public';
    message = `Are you sure you want to make "${name}" ${groupDescription}? ${count} ${pluralize(count, 'annotation that is', 'annotations that are')} visible only to members of "${name}" will become publicly visible.`;
  }

  return (
    <WarningDialog
      title={title}
      message={message}
      confirmAction={confirmAction}
      onConfirm={onConfirm}
      onCancel={onCancel}
    />
  );
}

export default function CreateEditGroupForm() {
  const config = useMemo(() => readConfig(), []);
  const group = config.context.group;

  const [name, setName] = useState(group?.name ?? '');
  const [description, setDescription] = useState(group?.description ?? '');
  const [groupType, setGroupType] = useState<GroupType>(
    group?.type ?? 'private',
  );

  // Set when the user selects a new group type if confirmation is required.
  // Cleared after confirmation.
  const [pendingGroupType, setPendingGroupType] = useState<GroupType | null>(
    null,
  );

  const [errorMessage, setErrorMessage] = useState('');
  const [saveState, setSaveState] = useState<
    'unmodified' | 'unsaved' | 'saving' | 'saved'
  >('unmodified');

  // Warn when leaving page if there are unsaved changes. We only do this when
  // editing a group because this hook lacks a way to disable the handler before
  // calling `setLocation` after a successful group creation.
  useWarnOnPageUnload(!!group && ['unsaved', 'saving'].includes(saveState));

  useEffect(() => {
    const listener = (e: PageTransitionEvent) => {
      if (e.persisted) {
        setSaveState('unmodified');
      }
    };
    window.addEventListener('pageshow', listener);
    return () => window.removeEventListener('pageshow', listener);
  }, []);

  const handleChangeName = (newName: string) => {
    setName(newName);
    setSaveState('unsaved');
  };

  const handleChangeDescription = (newDescription: string) => {
    setDescription(newDescription);
    setSaveState('unsaved');
  };

  const createGroup = async (e: SubmitEvent) => {
    e.preventDefault();
    setErrorMessage('');

    let response: CreateUpdateGroupAPIResponse;

    setSaveState('saving');

    try {
      const body: CreateUpdateGroupAPIRequest = {
        name,
        description,
        type: groupType,
      };

      response = (await callAPI(config.api.createGroup.url, {
        method: config.api.createGroup.method,
        headers: config.api.createGroup.headers,
        json: body,
      })) as CreateUpdateGroupAPIResponse;
    } catch (apiError) {
      setErrorMessage(apiError.message);
      setSaveState('unsaved');
      return;
    }

    setLocation(response.links.html);
  };

  const updateGroup = async (e: SubmitEvent) => {
    e.preventDefault();
    setErrorMessage('');
    setSaveState('saving');

    let response: CreateUpdateGroupAPIResponse;

    try {
      const body: CreateUpdateGroupAPIRequest = {
        id: group!.pubid,
        name,
        description,
        type: groupType,
      };

      response = (await callAPI(config.api.updateGroup!.url, {
        method: config.api.updateGroup!.method,
        headers: config.api.updateGroup!.headers,
        json: body,
      })) as CreateUpdateGroupAPIResponse;

      // Mark form as saved, unless user edited it while saving.
      setSaveState(state => (state === 'saving' ? 'saved' : state));
    } catch (apiError) {
      setSaveState('unsaved');
      setErrorMessage(apiError.message);
    }
  };

  let onSubmit;
  if (group) {
    onSubmit = updateGroup;
  } else {
    onSubmit = createGroup;
  }

  let heading;
  if (group) {
    heading = 'Edit group';
  } else if (config.features.group_type) {
    heading = 'Create a new group';
  } else {
    heading = 'Create a new private group';
  }

  const groupTypeLabel = useId();

  const changeGroupType = (newType: GroupType) => {
    const count = group?.num_annotations ?? 0;
    const oldTypeIsPrivate = groupType === 'private';
    const newTypeIsPrivate = newType === 'private';

    if (count === 0 || oldTypeIsPrivate === newTypeIsPrivate) {
      setGroupType(newType);
      setSaveState('unsaved');
    } else {
      setPendingGroupType(newType);
    }
  };

  return (
    <div className="text-grey-6 text-sm/relaxed">
      <h1 className="mt-14 mb-8 text-grey-7 text-xl/none" data-testid="header">
        {heading}
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

        {config.features.group_type && (
          <>
            <Label id={groupTypeLabel} text="Group type" />
            <RadioGroup
              aria-labelledby={groupTypeLabel}
              data-testid="group-type"
              direction="vertical"
              selected={groupType}
              onChange={changeGroupType}
            >
              <RadioGroup.Radio
                value="private"
                subtitle="Only members can create and read annotations."
              >
                Private
              </RadioGroup.Radio>
              <RadioGroup.Radio
                value="restricted"
                subtitle="Only members can create annotations, anyone can read them."
              >
                Restricted
              </RadioGroup.Radio>
              <RadioGroup.Radio
                value="open"
                subtitle="Anyone can create and read annotations."
              >
                Open
              </RadioGroup.Radio>
            </RadioGroup>
          </>
        )}

        <div className="flex items-center gap-x-4 mt-2">
          <div data-testid="error-container" role="alert">
            {errorMessage && (
              <div
                className="text-red-error font-bold flex items-center gap-x-2"
                data-testid="error-message"
              >
                <CancelIcon />
                {errorMessage}
              </div>
            )}
          </div>
          <div className="grow" />
          <SaveStateIcon
            state={saveState === 'unmodified' ? 'unsaved' : saveState}
          />
          <Button
            type="submit"
            variant="primary"
            disabled={saveState === 'saving'}
            data-testid="button"
          >
            {group ? 'Save changes' : 'Create group'}
          </Button>
        </div>
      </form>

      {group && pendingGroupType && (
        <GroupTypeChangeWarning
          name={name}
          newType={pendingGroupType}
          annotationCount={group.num_annotations}
          onCancel={() => setPendingGroupType(null)}
          onConfirm={() => {
            setGroupType(pendingGroupType);
            setSaveState('unsaved');
            setPendingGroupType(null);
          }}
        />
      )}

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
