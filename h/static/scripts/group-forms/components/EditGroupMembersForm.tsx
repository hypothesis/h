import { useContext } from 'preact/hooks';

import { Config } from '../config';
import FormContainer from './forms/FormContainer';
import GroupFormHeader from './GroupFormHeader';

export default function EditGroupMembersForm() {
  const config = useContext(Config)!;
  const group = config.context.group!;

  return (
    <FormContainer title="Edit group members">
      <GroupFormHeader group={group} />
      <hr />
      <div className="my-2">Group members will appear here.</div>
    </FormContainer>
  );
}
