import { mount, waitFor, waitForElement } from '@hypothesis/frontend-testing';
import { Select } from '@hypothesis/frontend-shared';

import { Config } from '../../config';
import {
  $imports,
  default as EditGroupMembersForm,
} from '../EditGroupMembersForm';

describe('EditGroupMembersForm', () => {
  let config;
  let fakeCallAPI;

  const defaultMembers = [
    {
      userid: 'acct:bob@localhost',
      username: 'bob',
      actions: [
        'delete',
        'updates.roles.admin',
        'updates.roles.moderator',
        'updates.roles.member',
      ],
      roles: ['admin'],
    },
    {
      userid: 'acct:johnsmith@localhost',
      username: 'johnsmith',
      actions: [],
      roles: ['owner'],
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
    },
  ];

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

    fakeCallAPI = sinon.stub();
    fakeCallAPI.rejects(new Error('Unknown API call'));
    fakeCallAPI.withArgs('/api/groups/1234/members').resolves(defaultMembers);
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
        <EditGroupMembersForm group={config.context.group} {...props} />
      </Config.Provider>,
    );
  };

  const waitForTable = wrapper =>
    waitForElement(wrapper, '[data-testid="username"]');

  const waitForError = wrapper =>
    waitFor(() => {
      wrapper.update();
      return wrapper.find('ErrorNotice').prop('message') !== null;
    });

  const getRenderedUsers = wrapper => {
    return wrapper.find('[data-testid="username"]').map(node => node.text());
  };

  const getRemoveUserButton = (wrapper, username) => {
    return wrapper.find(`IconButton[data-testid="remove-${username}"]`);
  };

  const getRoleSelect = (wrapper, username) => {
    return wrapper.find(`Select[data-testid="role-${username}"]`);
  };

  const getOptionValues = selectWrapper => {
    return selectWrapper
      .find(Select.Option)
      .map(option => option.prop('value'));
  };

  const getRoleText = (wrapper, username) => {
    return wrapper.find(`span[data-testid="role-${username}"]`);
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

    await waitForTable(wrapper);

    const users = getRenderedUsers(wrapper);
    assert.deepEqual(users, ['bob', 'johnsmith', 'jane']);
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
    assert.equal(error.prop('message'), 'User not found');
  });

  it('displays current and available user roles', async () => {
    const wrapper = createForm();
    await waitForTable(wrapper);

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
    assert.equal(error.prop('message'), 'Invalid role');

    // The displayed role should revert to the original value.
    wrapper.update();
    bobRole = getRoleSelect(wrapper, 'bob');
    assert.equal(bobRole.prop('value'), originalRole);
  });
});
