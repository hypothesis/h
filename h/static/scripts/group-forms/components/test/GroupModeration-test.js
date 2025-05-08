import { mount } from '@hypothesis/frontend-testing';

import GroupModeration from '../GroupModeration';

describe('GroupModeration', () => {
  function createComponent(groupName = 'The group') {
    return mount(<GroupModeration group={{ name: groupName }} />);
  }

  it('renders form header', () => {
    const wrapper = createComponent();
    assert.equal(
      wrapper.find('GroupFormHeader').prop('title'),
      'Moderate group',
    );
  });
});
