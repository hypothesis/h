import GroupFormHeader from './GroupFormHeader';
import type { Group } from '../config';
import FormContainer from './forms/FormContainer';

export type GroupModerationProps = {
  /** The group to be moderated */
  group: Group;
};

export default function GroupModeration({ group }: GroupModerationProps) {
  return (
    <FormContainer>
      <GroupFormHeader title="Moderate group" group={group} />
      <p>Moderate group {group.name}</p>
      <p>
        <i>TODO Annotations list</i>
      </p>
    </FormContainer>
  );
}
