import {
  DataTable,
  Scroll,
  TrashIcon,
  IconButton,
} from '@hypothesis/frontend-shared';
import { useContext, useEffect, useState } from 'preact/hooks';

import { Config } from '../config';
import type { APIConfig, Group } from '../config';
import ErrorNotice from './ErrorNotice';
import FormContainer from './forms/FormContainer';
import type { GroupMembersResponse } from '../utils/api';
import { callAPI } from '../utils/api';
import GroupFormHeader from './GroupFormHeader';
import WarningDialog from './WarningDialog';

type TableColumn<Row> = {
  field: keyof Row;
  label: string;
  classes?: string;
};

type MemberRow = {
  username: string;
  userid: string;
  showDeleteAction: boolean;
};

async function fetchMembers(
  api: APIConfig,
  currentUserid: string,
  signal: AbortSignal,
): Promise<MemberRow[]> {
  const { url, method, headers } = api;
  const members: GroupMembersResponse = await callAPI(url, {
    method,
    headers,
    signal,
  });
  return members.map(member => ({
    userid: member.userid,
    username: member.username,
    showDeleteAction:
      member.actions.includes('delete') && member.userid !== currentUserid,
  }));
}

async function removeMember(api: APIConfig, userid: string) {
  const { url: urlTemplate, method, headers } = api;
  const url = urlTemplate.replace(':userid', encodeURIComponent(userid));
  await callAPI(url, {
    method,
    headers,
  });
}

export type EditGroupMembersFormProps = {
  /** The saved group details. */
  group: Group;
};

export default function EditGroupMembersForm({
  group,
}: EditGroupMembersFormProps) {
  const config = useContext(Config)!;
  const userid = config.context.user.userid;

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
    fetchMembers(config.api.readGroupMembers, userid, abort.signal)
      .then(setMembers)
      .catch(err => {
        setErrorMessage(`Failed to fetch group members: ${err.message}`);
      });
    return () => {
      abort.abort();
    };
  }, [config.api.readGroupMembers, userid]);

  const columns: TableColumn<MemberRow>[] = [
    {
      field: 'username',
      label: 'Username',
    },
    {
      field: 'showDeleteAction',
      label: '',
      classes: 'w-[55px]',
    },
  ];

  const [pendingRemoval, setPendingRemoval] = useState<string | null>(null);

  const removeUserFromGroup = async (username: string) => {
    // istanbul ignore next
    if (!members || !config.api.removeGroupMember) {
      return;
    }
    const member = members.find(m => m.username === username);
    // istanbul ignore next
    if (!member) {
      return;
    }
    setPendingRemoval(null);

    try {
      await removeMember(config.api.removeGroupMember, member.userid);
      setMembers(members =>
        members ? members.filter(m => m.userid !== member.userid) : null,
      );
    } catch (err) {
      setErrorMessage(err.message);
    }
  };

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
      case 'showDeleteAction':
        return user.showDeleteAction ? (
          <IconButton
            icon={TrashIcon}
            title="Remove member"
            data-testid={`remove-${user.username}`}
            onClick={() => setPendingRemoval(user.username)}
          />
        ) : null;
      // istanbul ignore next
      default:
        return null;
    }
  };

  return (
    <>
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
      {pendingRemoval && (
        <WarningDialog
          title="Remove member?"
          confirmAction="Remove member"
          message={
            <p>
              Are you sure you want to remove <b>{pendingRemoval}</b> from the
              group?
            </p>
          }
          onConfirm={() => removeUserFromGroup(pendingRemoval)}
          onCancel={() => setPendingRemoval(null)}
        />
      )}
    </>
  );
}
