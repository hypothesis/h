import { checkAccessibility, mount } from '@hypothesis/frontend-testing';

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

  describe('moderation status filter', () => {
    it('shows pending status initially', () => {
      const wrapper = createComponent();
      assert.equal(
        wrapper.find('ModerationStatusSelect').prop('selected'),
        'pending',
      );
    });

    ['approved', 'denied', 'spam'].forEach(newStatus => {
      it('changes selected status on ModerationStatusSelect change', () => {
        const wrapper = createComponent();

        wrapper.find('ModerationStatusSelect').props().onChange(newStatus);
        wrapper.update();

        assert.equal(
          wrapper.find('ModerationStatusSelect').prop('selected'),
          newStatus,
        );
      });
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: () => createComponent() }),
  );
});
