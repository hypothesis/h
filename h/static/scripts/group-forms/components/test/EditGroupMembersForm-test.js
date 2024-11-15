import { waitFor, waitForElement } from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';

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
        <EditGroupMembersForm {...props} />
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

  it('fetches and displays members', async () => {
    const wrapper = createForm();
    assert.calledWith(fakeCallAPI, '/api/groups/1234/members');

    await waitForTable(wrapper);

    const users = wrapper.find('[data-testid="username"]');
    assert.equal(users.length, 1);
    assert.equal(users.at(0).text(), 'bob');
  });

  it('displays member count', async () => {
    const wrapper = createForm();
    const memberCount = wrapper.find('[data-testid="member-count"]');
    assert.equal(memberCount.text(), '... members');

    await waitForTable(wrapper);

    assert.equal(memberCount.text(), '1 member');
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
