import { DataTable, Scroll } from '@hypothesis/frontend-shared';
import { useContext, useEffect, useState } from 'preact/hooks';

import { Config } from '../config';
import { routes } from '../routes';
import ErrorNotice from './ErrorNotice';
import FormContainer from './forms/FormContainer';
import type { GroupMembersResponse } from '../utils/api';
import { callAPI } from '../utils/api';
import { pluralize } from '../utils/pluralize';
import GroupFormHeader from './GroupFormHeader';

type MemberRow = {
  username: string;
};

async function fetchMembers(
  groupid: string,
  signal: AbortSignal,
): Promise<MemberRow[]> {
  const membersURL = routes.api.group.members.replace(':pubid', groupid);
  const members: GroupMembersResponse = await callAPI(membersURL, { signal });
  return members.map(member => ({
    username: member.username,
  }));
}

export default function EditGroupMembersForm() {
  const config = useContext(Config)!;
  const group = config.context.group!;

  // Fetch group members when the form loads.
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [members, setMembers] = useState<MemberRow[] | null>(null);
  useEffect(() => {
    const abort = new AbortController();
    setErrorMessage(null);
    fetchMembers(group.pubid, abort.signal)
      .then(setMembers)
      .catch(err => {
        setErrorMessage(`Failed to fetch group members: ${err.message}`);
      });
    return () => {
      abort.abort();
    };
  }, [group.pubid]);

  const columns = [
    {
      field: 'username' as keyof MemberRow,
      label: 'Username',
    },
  ];

  const renderRow = (user: MemberRow, field: keyof MemberRow) => {
    switch (field) {
      case 'username':
        return (
          <div
            data-testid="username"
            className="truncate"
            title={user.username}
          >
            {user.username}
          </div>
        );
      // istanbul ignore next
      default:
        return null;
    }
  };

  const memberText = pluralize(members?.length ?? 0, 'member', 'members');

  return (
    <FormContainer title="Edit group members">
      <GroupFormHeader group={group} />
      <hr />
      <div className="flex py-3">
        <div className="grow" />
        <div data-testid="member-count">
          {members?.length ?? '...'} {memberText}
        </div>
      </div>
      <ErrorNotice message={errorMessage} />
      <div className="w-full">
        <Scroll>
          <DataTable
            title="Group members"
            rows={members ?? []}
            columns={columns}
            renderItem={renderRow}
          />
        </Scroll>
      </div>
    </FormContainer>
  );
}
