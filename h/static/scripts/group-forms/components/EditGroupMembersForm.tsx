import { DataTable, Input, Scroll } from '@hypothesis/frontend-shared';
import { useEffect, useMemo, useState } from 'preact/hooks';

import { routes } from '../routes';
import type { Group } from '../config';
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

export type EditGroupMembersFormProps = {
  /** The saved group details. */
  group: Group;
};

export default function EditGroupMembersForm({
  group,
}: EditGroupMembersFormProps) {
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

  const [filter, setFilter] = useState('');

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
  const normalizedFilter = filter.toLowerCase();

  const filteredMembers = useMemo(() => {
    if (!normalizedFilter || !members) {
      return members;
    }
    // nb. We can get away with lower-casing name and filter to do
    // case-insensitive search because of the character set restrictions on
    // usernames. This would be incorrect for Unicode text.
    return members.filter(m =>
      m.username.toLowerCase().includes(normalizedFilter),
    );
  }, [normalizedFilter, members]);

  let emptyMessage;
  if (members !== null && members.length > 0 && filter) {
    emptyMessage = (
      <div data-testid="no-filter-match">
        No members match the filter {'"'}
        <b>{filter}</b>
        {'"'}
      </div>
    );
  }

  return (
    <FormContainer title="Edit group members">
      <GroupFormHeader group={group} />
      <hr />
      <div className="flex py-3 items-center">
        {/* Input has `w-full` style. Wrap in container to stop it stretching to full width of row. */}
        <div>
          <Input
            aria-label="Search members"
            data-testid="search-input"
            placeholder="Search…"
            onInput={e => setFilter((e.target as HTMLInputElement).value)}
          />
        </div>
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
            rows={filteredMembers ?? []}
            columns={columns}
            renderItem={renderRow}
            emptyMessage={emptyMessage}
          />
        </Scroll>
      </div>
    </FormContainer>
  );
}
