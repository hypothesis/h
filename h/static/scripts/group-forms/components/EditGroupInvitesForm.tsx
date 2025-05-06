import type { Group } from '../config';
import FormContainer from './forms/FormContainer';
import GroupFormHeader from './GroupFormHeader';

export type EditGroupMembersFormProps = {
  /** The saved group details. */
  group: Group;
};

export default function EditGroupInvitesForm({
  group,
}: EditGroupMembersFormProps) {
  return (
    <>
      <FormContainer>
        <GroupFormHeader title="Group invites" group={group} />
        <p>Hello, world!</p>
      </FormContainer>
    </>
  );
}
