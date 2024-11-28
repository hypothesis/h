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
    config = {
      api: {
        readGroupMembers: {
          url: '/api/groups/1234/members',
          method: 'GET',
          headers: { 'Misc-Header': 'Some-Value' },
        },
      },
      context: {
        group: {
          pubid: '1234',
          name: 'Test group',
        },
      },
    };

    fakeCallAPI = sinon.stub();
    fakeCallAPI.withArgs('/api/groups/1234/members').resolves([
      {
        username: 'bob',
      },
      {
        username: 'johnsmith',
      },
    ]);

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
    assert.deepEqual(users, ['bob', 'johnsmith']);
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
