import {
  DataTable,
  Scroll,
  TrashIcon,
  IconButton,
  Select,
} from '@hypothesis/frontend-shared';
import { useContext, useEffect, useState } from 'preact/hooks';

import { Config } from '../config';
import type { APIConfig, Group } from '../config';
import type { GroupMember, GroupMembersResponse, Role } from '../utils/api';
import { callAPI } from '../utils/api';
import FormContainer from './forms/FormContainer';
import ErrorNotice from './ErrorNotice';
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

  /** Whether to show the button to remove this member from the group? */
  showDeleteAction: boolean;

  /** Current role for this user. */
  role: Role;

  /** Roles that can be assigned to this member. */
  availableRoles: Role[];

  /** True if an operation is currently being performed against this member. */
  busy: boolean;
};

/**
 * Mappings between roles and labels. The keys are sorted in descending order
 * of permissions.
 */
const roleStrings: Record<Role, string> = {
  owner: 'Owner',
  admin: 'Admin',
  moderator: 'Moderator',
  member: 'Member',
};
const possibleRoles: Role[] = Object.keys(roleStrings) as Role[];

function memberToRow(member: GroupMember, currentUserid: string): MemberRow {
  const role = member.roles[0] ?? 'member';
  const availableRoles =
    member.userid !== currentUserid
      ? possibleRoles.filter(role =>
          member.actions.includes(`updates.roles.${role}`),
        )
      : [role];
  return {
    userid: member.userid,
    username: member.username,
    showDeleteAction:
      member.actions.includes('delete') && member.userid !== currentUserid,
    role,
    availableRoles,
    busy: false,
  };
}

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
  return members.map(m => memberToRow(m, currentUserid));
}

async function removeMember(api: APIConfig, userid: string) {
  const { url: urlTemplate, method, headers } = api;
  const url = urlTemplate.replace(':userid', encodeURIComponent(userid));
  await callAPI(url, {
    method,
    headers,
  });
}

async function setMemberRoles(
  api: APIConfig,
  userid: string,
  roles: Role[],
): Promise<GroupMember> {
  const { url: urlTemplate, method, headers } = api;
  const url = urlTemplate.replace(':userid', encodeURIComponent(userid));
  return callAPI(url, {
    method,
    headers,
    json: {
      roles,
    },
  });
}

type RoleSelectProps = {
  username: string;

  disabled?: boolean;

  /** The current role of the member. */
  current: Role;

  /** Ordered list of possible roles that the current user can assign to the member. */
  available: Role[];

  /** Callback for when the user requests to change the role of the member. */
  onChange: (r: Role) => void;
};

function RoleSelect({
  username,
  disabled = false,
  current,
  available,
  onChange,
}: RoleSelectProps) {
  return (
    <Select
      value={current}
      onChange={onChange}
      buttonContent={roleStrings[current]}
      data-testid={`role-${username}`}
      disabled={disabled}
    >
      {available.map(role => (
        <Select.Option key={role} value={role}>
          {roleStrings[role]}
        </Select.Option>
      ))}
    </Select>
  );
}

export type EditGroupMembersFormProps = {
  /** The saved group details. */
  group: Group;
};

export default function EditGroupMembersForm({
  group,
}: EditGroupMembersFormProps) {
  const config = useContext(Config)!;
  const currentUserid = config.context.user.userid;

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
    fetchMembers(config.api.readGroupMembers, currentUserid, abort.signal)
      .then(setMembers)
      .catch(err => {
        setErrorMessage(`Failed to fetch group members: ${err.message}`);
      });
    return () => {
      abort.abort();
    };
  }, [config.api.readGroupMembers, currentUserid]);

  const columns: TableColumn<MemberRow>[] = [
    {
      field: 'username',
      label: 'Username',
    },
    {
      field: 'role',
      label: 'Role',
    },
    {
      field: 'showDeleteAction',
      label: '',
      classes: 'w-[55px]',
    },
  ];

  const [pendingRemoval, setPendingRemoval] = useState<string | null>(null);

  const updateMember = (userid: string, update: Partial<MemberRow>) => {
    setMembers(
      members =>
        members?.map(m => {
          return m.userid === userid ? { ...m, ...update } : m;
        }) ?? null,
    );
  };

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

    updateMember(member.userid, { busy: true });

    try {
      await removeMember(config.api.removeGroupMember, member.userid);
      setMembers(members =>
        members ? members.filter(m => m.userid !== member.userid) : null,
      );
    } catch (err) {
      updateMember(member.userid, { busy: false });
      setErrorMessage(err.message);
    }
  };

  const changeRole = async (member: MemberRow, role: Role) => {
    updateMember(member.userid, { role, busy: true });
    try {
      const updatedMember = await setMemberRoles(
        config.api.editGroupMember!,
        member.userid,
        [role],
      );
      // Update the member row in case the role change affected other columns
      // (eg. whether we have permission to delete the user).
      updateMember(member.userid, memberToRow(updatedMember, currentUserid));
    } catch (err) {
      const prevRole = member.role;
      updateMember(member.userid, { role: prevRole, busy: false });
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
      case 'role':
        if (user.availableRoles.length <= 1) {
          return (
            <span data-testid={`role-${user.username}`}>
              {roleStrings[user.role]}
            </span>
          );
        }
        return (
          <RoleSelect
            username={user.username}
            current={user.role}
            available={user.availableRoles}
            onChange={role => changeRole(user, role)}
            disabled={user.busy}
          />
        );
      case 'showDeleteAction':
        return user.showDeleteAction ? (
          <IconButton
            classes={user.busy ? 'opacity-50' : ''}
            disabled={user.busy}
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
              loading={!members}
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
