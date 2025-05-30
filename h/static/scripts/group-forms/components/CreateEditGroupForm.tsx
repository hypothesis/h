import {
  Button,
  RadioGroup,
  LockFilledIcon,
  GlobeIcon,
  GlobeLockIcon,
} from '@hypothesis/frontend-shared';
import { useContext, useEffect, useId, useState } from 'preact/hooks';

import { Config } from '../config';
import type { Group } from '../config';
import { callAPI } from '../utils/api';
import type {
  CreateUpdateGroupAPIRequest,
  CreateUpdateGroupAPIResponse,
  GroupType,
} from '../utils/api';
import { pluralize } from '../utils/pluralize';
import { setLocation } from '../utils/set-location';
import { useUnsavedChanges } from '../utils/unsaved-changes';
import ErrorNotice from './ErrorNotice';
import GroupFormHeader from './GroupFormHeader';
import SaveStateIcon from './SaveStateIcon';
import WarningDialog from './WarningDialog';
import Checkbox from './forms/Checkbox';
import FormContainer from './forms/FormContainer';
import Label from './forms/Label';
import Star from './forms/Star';
import TextField from './forms/TextField';

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

export type CreateEditGroupFormProps = {
  /** The saved group details, or `null` if the group has not been saved yet. */
  group: Group | null;

  /** Update the saved group details in the frontend's local state. */
  onUpdateGroup?: (g: Group) => void;
};

export default function CreateEditGroupForm({
  group,
  onUpdateGroup,
}: CreateEditGroupFormProps) {
  const config = useContext(Config)!;

  const [name, setName] = useState(group?.name ?? '');
  const [description, setDescription] = useState(group?.description ?? '');
  const [groupType, setGroupType] = useState<GroupType>(
    group?.type ?? 'private',
  );
  const initiallyPreModerated = group?.pre_moderated ?? false;
  const [preModerated, setPreModerated] = useState(initiallyPreModerated);

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
  useUnsavedChanges(!!group && ['unsaved', 'saving'].includes(saveState));

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
        pre_moderated: preModerated,
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

    try {
      const body: CreateUpdateGroupAPIRequest = {
        id: group!.pubid,
        name,
        description,
        type: groupType,
        pre_moderated: preModerated,
      };

      (await callAPI(config.api.updateGroup!.url, {
        method: config.api.updateGroup!.method,
        headers: config.api.updateGroup!.headers,
        json: body,
      })) as CreateUpdateGroupAPIResponse;

      // Mark form as saved, unless user edited it while saving.
      setSaveState(state => (state === 'saving' ? 'saved' : state));

      onUpdateGroup?.({ ...group!, name, description, type: groupType });
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
    <FormContainer>
      <GroupFormHeader group={group} title={heading} />
      <form
        onSubmit={onSubmit}
        data-testid="form"
        className="max-w-[530px] mx-auto flex flex-col gap-y-4"
      >
        <TextField
          type="input"
          value={name}
          onChangeValue={handleChangeName}
          minLength={3}
          maxLength={25}
          label="Name"
          autofocus
          required
        />
        <TextField
          type="textarea"
          value={description}
          onChangeValue={handleChangeDescription}
          maxLength={250}
          label="Description"
          classes="h-24"
        />

        {config.features.group_type && (
          <div>
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
                <LockFilledIcon /> Private
              </RadioGroup.Radio>
              <RadioGroup.Radio
                value="restricted"
                subtitle="Only members can create annotations, anyone can read them."
              >
                <GlobeLockIcon /> Restricted
              </RadioGroup.Radio>
              <RadioGroup.Radio
                value="open"
                subtitle="Anyone can create and read annotations."
              >
                <GlobeIcon /> Open
              </RadioGroup.Radio>
            </RadioGroup>
          </div>
        )}

        {config.features.pre_moderation && (
          <fieldset>
            <legend className="font-bold">Moderation</legend>
            <Checkbox
              data-testid="pre-moderation"
              checked={preModerated}
              onChange={e => {
                setPreModerated((e.target as HTMLInputElement).checked);
                setSaveState('unsaved');
              }}
              description="Moderators must approve new annotations before they are shown to group members."
            >
              Enable pre-moderation for this group.
            </Checkbox>
          </fieldset>
        )}

        <div className="pt-2 border-t border-t-text-grey-6 flex items-center gap-x-4">
          <span>
            {/* These are in a child span to avoid a gap between them. */}
            <Star />
            &nbsp;Required
          </span>
          <ErrorNotice message={errorMessage} />
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
    </FormContainer>
  );
}
