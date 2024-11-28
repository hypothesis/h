import { DataTable, Scroll } from '@hypothesis/frontend-shared';
import { useContext, useEffect, useState } from 'preact/hooks';

import { Config } from '../config';
import type { APIConfig, Group } from '../config';
import ErrorNotice from './ErrorNotice';
import FormContainer from './forms/FormContainer';
import type { GroupMembersResponse } from '../utils/api';
import { callAPI } from '../utils/api';
import GroupFormHeader from './GroupFormHeader';

type MemberRow = {
  username: string;
};

async function fetchMembers(
  api: APIConfig,
  signal: AbortSignal,
): Promise<MemberRow[]> {
  const { url, method, headers } = api;
  const members: GroupMembersResponse = await callAPI(url, {
    method,
    headers,
    signal,
  });
  return members.map(member => ({
    username: member.username,
  }));
}

export type EditGroupMembersFormProps = {
  /** The saved group details. */
  group: Group;
};

export default function EditGroupMembersForm({
  group,
}: EditGroupMembersFormProps) {
  const config = useContext(Config)!;

  // Fetch group members when the form loads.
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [members, setMembers] = useState<MemberRow[] | null>(null);
  useEffect(() => {
    // istanbul ignore next
    if (!config.api.readGroupMembers) {
      throw new Error('readGroupMembers API config missing');
    }
    const abort = new AbortController();
    setErrorMessage(null);
    fetchMembers(config.api.readGroupMembers, abort.signal)
      .then(setMembers)
      .catch(err => {
        setErrorMessage(`Failed to fetch group members: ${err.message}`);
      });
    return () => {
      abort.abort();
    };
  }, [config.api.readGroupMembers]);

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

  return (
    <FormContainer title="Edit group members">
      <GroupFormHeader group={group} />
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
