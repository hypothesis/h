import {
  delay,
  mount,
  waitFor,
  waitForElement,
} from '@hypothesis/frontend-testing';
import { Select } from '@hypothesis/frontend-shared';
import { act } from 'preact/test-utils';

import { APIError } from '../../utils/api';
import { Config } from '../../config';
import {
  $imports,
  default as EditGroupMembersForm,
  pageSize,
} from '../EditGroupMembersForm';

describe('EditGroupMembersForm', () => {
  let config;
  let dateFormatter;
  let fakeCallAPI;

  const defaultMembers = [
    {
      userid: 'acct:bob@localhost',
      username: 'bob',
      display_name: 'Bob Jones',
      actions: [
        'delete',
        'updates.roles.admin',
        'updates.roles.moderator',
        'updates.roles.member',
      ],
      roles: ['admin'],

      // User who joined before Dec 2024
      created: null,
    },
    {
      userid: 'acct:johnsmith@localhost',
      username: 'johnsmith',
      display_name: 'John Smith',
      actions: [],
      roles: ['owner'],
      created: '2024-01-01T01:02:03+00:00',
    },
    {
      userid: 'acct:jane@localhost',
      username: 'jane',
      actions: [
        'delete',
        'updates.roles.admin',
        'updates.roles.moderator',
        'updates.roles.member',
      ],
      roles: ['admin'],
      created: '2024-01-02T01:02:03+00:00',
    },
  ];

  const listMembersResponse = (members, total = members.length) => {
    return {
      meta: {
        page: {
          total,
        },
      },
      data: members,
    };
  };

  beforeEach(() => {
    const headers = { 'Misc-Header': 'Some-Value' };
    config = {
      api: {
        readGroupMembers: {
          url: '/api/groups/1234/members',
          method: 'GET',
          headers,
        },
        editGroupMember: {
          url: '/api/groups/1234/members/:userid',
          method: 'PATCH',
          headers,
        },
        removeGroupMember: {
          url: '/api/groups/1234/members/:userid',
          method: 'DELETE',
          headers,
        },
      },
      context: {
        group: {
          pubid: '1234',
          name: 'Test group',
        },
        user: {
          userid: 'acct:jane@localhost',
        },
      },
    };

    dateFormatter = {
      format(date) {
        // Return date in YYYY-MM-DD format.
        return date.toISOString().match(/[0-9-]+/)[0];
      },
    };

    fakeCallAPI = sinon.stub();
    fakeCallAPI.rejects(new Error('Unknown API call'));
    fakeCallAPI
      .withArgs('/api/groups/1234/members')
      .resolves(listMembersResponse(defaultMembers));
    fakeCallAPI
      .withArgs(
        `/api/groups/1234/members/${encodeURIComponent('acct:bob@localhost')}`,
        sinon.match({
          method: 'DELETE',
        }),
      )
      .resolves({});

    fakeCallAPI
      .withArgs(
        `/api/groups/1234/members/${encodeURIComponent('acct:bob@localhost')}`,
        sinon.match({
          method: 'PATCH',
        }),
      )
      .callsFake(async (url, { json }) => {
        const updatedMember = {
          ...defaultMembers.find(m => m.username === 'bob'),
        };
        updatedMember.roles = [...json.roles];
        return updatedMember;
      });

    $imports.$mock({
      '../utils/api': {
        callAPI: fakeCallAPI,
      },
    });
  });

  const createForm = (props = {}) => {
    return mount(
      <Config.Provider value={config}>
        <EditGroupMembersForm
          group={config.context.group}
          dateFormatter={dateFormatter}
          {...props}
        />
      </Config.Provider>,
      { connected: true },
    );
  };

  const waitForTable = wrapper =>
    waitForElement(wrapper, '[data-testid="username"]');

  const waitForError = wrapper =>
    waitFor(() => {
      wrapper.update();
      return wrapper.find('ErrorNotice').prop('message') !== null;
    });

  const getRenderedUsernames = wrapper => {
    return wrapper.find('[data-testid="username"]').map(node => node.text());
  };

  const getRenderedDisplayNames = wrapper => {
    return wrapper
      .find('[data-testid="display-name"]')
      .map(node => node.text());
  };

  const getRenderedJoinDate = (wrapper, username) => {
    return wrapper.find(`[data-testid="joined-${username}"]`).text();
  };

  const getRemoveUserButton = (wrapper, username) => {
    return wrapper.find(`IconButton[data-testid="remove-${username}"]`);
  };

  const getRoleSelect = (wrapper, username) => {
    return wrapper.find(`Select[data-testid="role-${username}"]`);
  };

  const openRoleSelect = (wrapper, username) => {
    getRoleSelect(wrapper, username).find('button').simulate('click');
  };

  const getPaginationState = wrapper => {
    const pagination = wrapper.find('Pagination');
    if (!pagination.exists()) {
      return null;
    }
    return {
      current: pagination.prop('currentPage'),
      total: pagination.prop('totalPages'),
    };
  };

  /**
   * Return the roles listed in a given select. Note that the select must be
   * open for the options to be rendered.
   */
  const getOptionValues = selectWrapper => {
    return selectWrapper
      .find(Select.Option)
      .map(option => option.prop('value'));
  };

  const getRoleText = (wrapper, username) => {
    return wrapper.find(`span[data-testid="role-${username}"]`);
  };

  /**
   * Return true if controls to edit a given member are all disabled, or there
   * are no controls for the member.
   */
  const controlsDisabled = (wrapper, username) => {
    const removeButton = getRemoveUserButton(wrapper, username);
    const roleSelect = getRoleSelect(wrapper, username);
    return [removeButton, roleSelect].every(
      control => !control.exists() || control.prop('disabled'),
    );
  };

  /** Construct an APIError corresponding to an aborted request. */
  const abortError = () => {
    const abortError = new Error('Aborted');
    abortError.name = 'AbortError';
    return new APIError('Something went wrong', {
      cause: abortError,
    });
  };

  it('fetches and displays members', async () => {
    const wrapper = createForm();
    assert.calledWith(
      fakeCallAPI,
      '/api/groups/1234/members',
      sinon.match({
        method: config.api.readGroupMembers.method,
        headers: config.api.readGroupMembers.headers,
      }),
    );
    assert.isTrue(wrapper.find('DataTable').prop('loading'));

    await waitForTable(wrapper);

    assert.isFalse(wrapper.find('DataTable').prop('loading'));
    const usernames = getRenderedUsernames(wrapper);
    assert.deepEqual(usernames, ['@bob', '@johnsmith', '@jane']);

    const displayNames = getRenderedDisplayNames(wrapper);
    assert.deepEqual(displayNames, ['Bob Jones', 'John Smith']);

    assert.equal(getRenderedJoinDate(wrapper, 'bob'), '');
    assert.equal(getRenderedJoinDate(wrapper, 'johnsmith'), '2024-01-01');
    assert.equal(getRenderedJoinDate(wrapper, 'jane'), '2024-01-02');
  });

  [
    {
      total: 5,
      pagination: null,
    },
    {
      total: pageSize + 5,
      pagination: {
        current: 1,
        total: 2,
      },
    },
  ].forEach(({ total, pagination: expectedPagination }) => {
    it('displays pagination controls', async () => {
      fakeCallAPI
        .withArgs('/api/groups/1234/members')
        .resolves(listMembersResponse(defaultMembers, total));
      const wrapper = createForm();
      await waitForTable(wrapper);
      const pagination = getPaginationState(wrapper);
      assert.deepEqual(pagination, expectedPagination);
    });
  });

  it('navigates when page is changed', async () => {
    fakeCallAPI
      .withArgs('/api/groups/1234/members')
      .resolves(listMembersResponse(defaultMembers, pageSize + 5));
    const wrapper = createForm();
    await waitForTable(wrapper);

    assert.deepEqual(getPaginationState(wrapper), {
      current: 1,
      total: 2,
    });

    act(() => {
      wrapper.find('Pagination').prop('onChangePage')(2);
    });
    wrapper.update();
    assert.calledWith(
      fakeCallAPI,
      '/api/groups/1234/members',
      sinon.match({
        pageNumber: 2,
        pageSize: pageSize,
      }),
    );

    assert.deepEqual(getPaginationState(wrapper), {
      current: 2,
      total: 2,
    });
  });

  it('displays error if member fetch fails', async () => {
    fakeCallAPI
      .withArgs('/api/groups/1234/members')
      .rejects(new Error('Permission denied'));

    const wrapper = createForm();
    await waitForError(wrapper);

    const error = wrapper.find('ErrorNotice');
    assert.equal(
      error.prop('message'),
      'Failed to fetch group members: Permission denied',
    );
  });

  // Don't show an error if fetching members is canceled due to a navigation
  // (eg. page change) happening during the fetch.
  it('does not display error if member fetch is aborted', async () => {
    fakeCallAPI.withArgs('/api/groups/1234/members').rejects(abortError());
    const wrapper = createForm();

    await delay(0);

    wrapper.update();
    assert.equal(wrapper.find('ErrorNotice').prop('message'), null);
    assert.deepEqual(getRenderedUsernames(wrapper), []);
  });

  it('handles member fetch being canceled', () => {
    const wrapper = createForm();
    assert.calledWith(fakeCallAPI, '/api/groups/1234/members');
    // Unmount while fetching. This should abort the request.
    wrapper.unmount();
  });

  it('displays remove icon if member can be removed', async () => {
    const wrapper = createForm();
    await waitForTable(wrapper);

    const expectRemovable = {
      bob: true, // `delete` action present in `actions`
      johnsmith: false, // `delete` action present in `actions`
      jane: false, // `delete` action present, but this is the current user
    };

    for (const [username, removable] of Object.entries(expectRemovable)) {
      const removeButton = getRemoveUserButton(wrapper, username);
      assert.equal(removeButton.exists(), removable);
    }
  });

  it('removes user with confirmation if remove button is clicked', async () => {
    const wrapper = createForm();
    await waitForTable(wrapper);
    const removeBob = getRemoveUserButton(wrapper, 'bob');

    removeBob.prop('onClick')();
    wrapper.update();

    // Confirmation prompt should be shown.
    const warning = wrapper.find('WarningDialog');
    assert.isTrue(warning.exists());

    // Canceling the prompt should hide the dialog.
    warning.prop('onCancel')();
    wrapper.update();
    assert.isFalse(wrapper.exists('WarningDialog'));

    // Confirming the prompt should hide the dialog and trigger a call to
    // remove the user.
    removeBob.prop('onClick')();
    wrapper.update();
    warning.prop('onConfirm')();
    wrapper.update();
    assert.isFalse(wrapper.exists('WarningDialog'));

    // Controls should be disabled while API call is in flight.
    assert.isTrue(controlsDisabled(wrapper, 'bob'));

    // Once the user is removed, their row should disappear.
    await waitFor(() => {
      wrapper.update();
      return !getRemoveUserButton(wrapper, 'bob').exists();
    });
  });

  it('shows error if removing user fails', async () => {
    const userid = 'acct:bob@localhost';
    fakeCallAPI
      .withArgs(
        `/api/groups/1234/members/${encodeURIComponent(userid)}`,
        sinon.match({
          method: 'DELETE',
        }),
      )
      .rejects(new Error('User not found'));

    const wrapper = createForm();
    await waitForTable(wrapper);
    const removeBob = getRemoveUserButton(wrapper, 'bob');
    removeBob.prop('onClick')();
    wrapper.update();
    wrapper.find('WarningDialog').prop('onConfirm')();

    await waitForError(wrapper);
    const error = wrapper.find('ErrorNotice');
    assert.equal(
      error.prop('message'),
      'Failed to remove member: User not found',
    );

    // Controls should be re-enabled after saving fails.
    assert.include(getRenderedUsernames(wrapper), '@bob');
    assert.isFalse(controlsDisabled(wrapper, 'bob'));
  });

  it('displays current and available user roles', async () => {
    const wrapper = createForm();
    await waitForTable(wrapper);

    openRoleSelect(wrapper, 'bob');

    // If the user's role can be changed, the current role and available options
    // should be displayed in a Select.
    const bobRole = getRoleSelect(wrapper, 'bob');
    assert.isTrue(bobRole.exists());
    assert.equal(bobRole.prop('value'), 'admin');
    assert.deepEqual(getOptionValues(bobRole), [
      'admin',
      'moderator',
      'member',
    ]);

    // If the user's role cannot be changed, the current role should be
    // displayed as text.
    const johnRoleSelect = getRoleSelect(wrapper, 'johnsmith');
    assert.isFalse(johnRoleSelect.exists());
    const johnRoleText = getRoleText(wrapper, 'johnsmith');
    assert.equal(johnRoleText.text(), 'Owner');

    // The role for the current user should be displayed as text, even if the
    // API would allow changing our own role.
    const janeRoleSelect = getRoleSelect(wrapper, 'jane');
    assert.isFalse(janeRoleSelect.exists());
    const janeRoleText = getRoleText(wrapper, 'jane');
    assert.equal(janeRoleText.text(), 'Admin');
  });

  it('updates user role when select value is changed', async () => {
    const wrapper = createForm();
    await waitForTable(wrapper);
    let bobRole = getRoleSelect(wrapper, 'bob');
    bobRole.prop('onChange')('moderator');

    // The displayed role should update immediately when the new role is
    // selected.
    wrapper.update();
    bobRole = getRoleSelect(wrapper, 'bob');
    assert.equal(bobRole.prop('value'), 'moderator');

    assert.calledWith(
      fakeCallAPI,
      `/api/groups/1234/members/${encodeURIComponent('acct:bob@localhost')}`,
      sinon.match({
        method: 'PATCH',
        json: {
          roles: ['moderator'],
        },
      }),
    );

    // Controls should be disabled while saving.
    assert.isTrue(controlsDisabled(wrapper, 'bob'));

    await waitFor(() => {
      wrapper.update();
      return !controlsDisabled(wrapper, 'bob');
    });

    // New role should be preserved once save completes.
    bobRole = getRoleSelect(wrapper, 'bob');
    assert.equal(bobRole.prop('value'), 'moderator');
  });

  it('displays error if changing role fails', async () => {
    fakeCallAPI
      .withArgs(
        `/api/groups/1234/members/${encodeURIComponent('acct:bob@localhost')}`,
        sinon.match({
          method: 'PATCH',
        }),
      )
      .rejects(new Error('Invalid role'));
    const wrapper = createForm();
    await waitForTable(wrapper);

    // Attempt to change the role
    let bobRole = getRoleSelect(wrapper, 'bob');
    const originalRole = bobRole.prop('value');
    bobRole.prop('onChange')('moderator');
    wrapper.update();

    // The role should briefly change to the new selection.
    assert.equal(getRoleSelect(wrapper, 'bob').prop('value'), 'moderator');

    // Wait for the role change to fail. An error should be displayed.
    await waitForError(wrapper);
    const error = wrapper.find('ErrorNotice');
    assert.equal(
      error.prop('message'),
      'Failed to change member role: Invalid role',
    );

    // The displayed role should revert to the original value.
    wrapper.update();
    bobRole = getRoleSelect(wrapper, 'bob');
    assert.equal(bobRole.prop('value'), originalRole);
    assert.isFalse(controlsDisabled(wrapper, 'bob'));
  });
});
