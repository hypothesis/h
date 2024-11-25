import { mount, waitFor, waitForElement } from '@hypothesis/frontend-testing';

import { Config } from '../../config';
import {
  $imports,
  default as EditGroupMembersForm,
} from '../EditGroupMembersForm';

describe('EditGroupMembersForm', () => {
  let config;
  let fakeCallAPI;

  beforeEach(() => {
    const headers = { 'Misc-Header': 'Some-Value' };
    config = {
      api: {
        readGroupMembers: {
          url: '/api/groups/1234/members',
          method: 'GET',
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
    fakeCallAPI.withArgs('/api/groups/1234/members').resolves([
      {
        userid: 'acct:bob@localhost',
        username: 'bob',
        actions: ['delete'],
      },
      {
        userid: 'acct:johnsmith@localhost',
        username: 'johnsmith',
        actions: [],
      },
      {
        userid: 'acct:jane@localhost',
        username: 'jane',
        actions: ['delete'],
      },
    ]);

    fakeCallAPI
      .withArgs(
        `/api/groups/1234/members/${encodeURIComponent('acct:bob@localhost')}`,
        sinon.match({
          method: 'DELETE',
        }),
      )
      .resolves({});

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
});
