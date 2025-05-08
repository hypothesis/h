import {
  DataTable,
  Scroll,
  TrashIcon,
  IconButton,
  Pagination,
  Select,
} from '@hypothesis/frontend-shared';
import { useCallback, useContext, useEffect, useState } from 'preact/hooks';

import { Config } from '../config';
import type { APIConfig, Group } from '../config';
import { paginationToParams } from '../utils/api';
import { callAPI } from '../utils/api';
import type {
  APIError,
  GroupMember,
  GroupMembersResponse,
  Role,
} from '../utils/api';
import ErrorNotice from './ErrorNotice';
import GroupFormHeader from './GroupFormHeader';
import WarningDialog from './WarningDialog';
import FormContainer from './forms/FormContainer';

type TableColumn<Row> = {
  field: keyof Row;
  label: string;
  classes?: string;
};

type MemberRow = {
  userid: string;

  username: string;
  displayName?: string;

  /** Whether to show the button to remove this member from the group? */
  showDeleteAction: boolean;

  /** Current role for this user. */
  role: Role;

  /** Roles that can be assigned to this member. */
  availableRoles: Role[];

  /** True if an operation is currently being performed against this member. */
  busy: boolean;

  /** Date when user joined group, if known. */
  joined?: Date;
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
    displayName: member.display_name,
    username: member.username,
    showDeleteAction:
      member.actions.includes('delete') && member.userid !== currentUserid,
    role,
    availableRoles,
    busy: false,
    joined: member.created ? new Date(member.created) : undefined,
  };
}

async function fetchMembers(
  api: APIConfig,
  currentUserid: string,
  options: {
    signal: AbortSignal;
    pageNumber: number;
    pageSize: number;
  },
): Promise<{ total: number; members: MemberRow[] }> {
  const { pageNumber, pageSize, signal } = options;
  const { url, method, headers } = api;
  const query = paginationToParams({ pageNumber, pageSize });
  const { meta, data }: GroupMembersResponse = await callAPI(url, {
    headers,
    query,
    method,
    signal,
  });

  return {
    total: meta.page.total,
    members: data.map(m => memberToRow(m, currentUserid)),
  };
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
      aria-label="Select role"
    >
      {available.map(role => (
        <Select.Option key={role} value={role}>
          {roleStrings[role]}
        </Select.Option>
      ))}
    </Select>
  );
}

const defaultDateFormatter = new Intl.DateTimeFormat(undefined, {
  year: 'numeric',
  month: 'short',
  day: '2-digit',
});

export const pageSize = 20;

export type EditGroupMembersFormProps = {
  /** The saved group details. */
  group: Group;

  /** Test seam. Formatter used to format the "Joined" date. */
  dateFormatter?: Intl.DateTimeFormat;
};

export default function EditGroupMembersForm({
  group,
  dateFormatter = defaultDateFormatter,
}: EditGroupMembersFormProps) {
  const config = useContext(Config)!;
  const currentUserid = config.context.user.userid;

  const [pageNumber, setPageNumber] = useState(1);
  const [totalMembers, setTotalMembers] = useState<number | null>(null);
  const totalPages =
    totalMembers !== null ? Math.ceil(totalMembers / pageSize) : null;
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const setError = useCallback((context: string, err: Error) => {
    const apiErr = err as APIError;
    if (apiErr.aborted) {
      return;
    }
    const message = `${context}: ${err.message}`;
    setErrorMessage(message);
  }, []);

  // Fetch group members when the form loads.
  const [members, setMembers] = useState<MemberRow[] | null>(null);
  useEffect(() => {
    // istanbul ignore next
    if (!config.api.readGroupMembers) {
      throw new Error('readGroupMembers API config missing');
    }
    const abort = new AbortController();
    setErrorMessage(null);
    fetchMembers(config.api.readGroupMembers, currentUserid, {
      pageNumber,
      pageSize,
      signal: abort.signal,
    })
      .then(({ total, members }) => {
        setMembers(members);
        setTotalMembers(total);
      })
      .catch(err => {
        setError('Failed to fetch group members', err);
      });
    return () => {
      abort.abort();
    };
  }, [config.api.readGroupMembers, currentUserid, pageNumber, setError]);

  const columns: TableColumn<MemberRow>[] = [
    {
      field: 'username',
      label: 'Username',
    },
    {
      field: 'role',
      label: 'Role',
      classes: 'w-40',
    },
    {
      field: 'joined',
      label: 'Joined',
      classes: 'w-36',
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
      setError('Failed to remove member', err);
    }
  };

  const changeRole = useCallback(
    async (member: MemberRow, role: Role) => {
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
        setError('Failed to change member role', err);
      }
    },
    [currentUserid, config.api.editGroupMember, setError],
  );

  const renderRow = useCallback(
    (user: MemberRow, field: keyof MemberRow) => {
      switch (field) {
        case 'username':
          return (
            <div className="truncate" title={user.username}>
              <span data-testid="username" className="font-bold text-grey-7">
                @{user.username}
              </span>
              {user.displayName && (
                <span data-testid="display-name">
                  {
                    // Create space using a separate element, rather than eg.
                    // `inline-block ml-3` on the display name container because
                    // that would cause the entire display name to be hidden if
                    // truncated.
                    <span className="inline-block w-3" />
                  }
                  {user.displayName}
                </span>
              )}
            </div>
          );
        case 'role':
          if (user.availableRoles.length <= 1) {
            return (
              // Left padding here aligns the static role label in this row with
              // the current role in dropdowns in other rows.
              <span className="pl-2" data-testid={`role-${user.username}`}>
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
        case 'joined':
          return (
            <span data-testid={`joined-${user.username}`}>
              {user.joined && dateFormatter.format(user.joined)}
            </span>
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
    },
    [changeRole, dateFormatter],
  );

  return (
    <>
      <FormContainer>
        <GroupFormHeader title="Edit group members" group={group} />
        <ErrorNotice message={errorMessage} />
        <div className="w-full">
          <Scroll>
            <DataTable
              grid
              striped={false}
              title="Group members"
              rows={members ?? []}
              columns={columns}
              renderItem={renderRow}
              loading={!members}
            />
          </Scroll>
        </div>
        {typeof totalPages === 'number' && totalPages > 1 && (
          <div className="mt-4 flex justify-center">
            <Pagination
              currentPage={pageNumber}
              onChangePage={setPageNumber}
              totalPages={totalPages}
            />
          </div>
        )}
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
