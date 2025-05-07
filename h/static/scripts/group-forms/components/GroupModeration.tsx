import { useState } from 'preact/hooks';

import type { Group } from '../config';
import GroupFormHeader from './GroupFormHeader';
import type { ModerationStatus } from './ModerationStatusSelect';
import ModerationStatusSelect from './ModerationStatusSelect';
import FormContainer from './forms/FormContainer';

export type GroupModerationProps = {
  /** The group to be moderated */
  group: Group;
};

export default function GroupModeration({ group }: GroupModerationProps) {
  const [filterStatus, setFilterStatus] = useState<
    ModerationStatus | undefined
  >('pending');

  return (
    <FormContainer>
      <GroupFormHeader title="Moderate group" group={group} />
      <div className="flex justify-end">
        <ModerationStatusSelect
          selected={filterStatus}
          onChange={setFilterStatus}
        />
      </div>
      <p>Moderate group {group.name}</p>
      <p>
        <i>TODO Annotations list</i>
      </p>
    </FormContainer>
  );
}
