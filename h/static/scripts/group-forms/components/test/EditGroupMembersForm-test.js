import { mount } from 'enzyme';

import { Config } from '../../config';
import EditGroupMembersForm from '../EditGroupMembersForm';

describe('EditGroupMembersForm', () => {
  let config;

  beforeEach(() => {
    config = {
      context: {
        group: {
          pubid: '1234',
          name: 'Test group',
        },
      },
    };
  });

  const createForm = (props = {}) => {
    return mount(
      <Config.Provider value={config}>
        <EditGroupMembersForm {...props} />
      </Config.Provider>,
    );
  };

  it('renders', () => {
    createForm();
  });
});
