import { checkAccessibility, mount } from '@hypothesis/frontend-testing';

import GroupFormHeader from '../GroupFormHeader';

describe('GroupFormHeader', () => {
  const createHeader = (props = {}) => mount(<GroupFormHeader {...props} />);

  const group = {
    pubid: 'abc123',
    link: 'https://anno.co/groups/abc123',
  };

  const getLink = (wrapper, name) => wrapper.find(`a[data-testid="${name}"]`);

  it('renders title', () => {
    const header = createHeader({ title: 'Create a new group' });
    assert.equal(header.find('h1').text(), 'Create a new group');
  });

  it('does not show activity link or tabs if no group', () => {
    const header = createHeader();
    assert.isFalse(getLink(header, 'activity-link').exists());
    assert.isFalse(getLink(header, 'settings-link').exists());
    assert.isFalse(getLink(header, 'members-link').exists());
  });

  it('renders group activity link and tabs if there is a group', () => {
    const header = createHeader({ group });

    const activityLink = getLink(header, 'activity-link');
    assert.equal(activityLink.prop('href'), group.link);

    const settingsLink = getLink(header, 'settings-link');
    assert.equal(settingsLink.prop('href'), '/groups/abc123/edit');

    const membersLink = getLink(header, 'members-link');
    assert.equal(membersLink.prop('href'), '/groups/abc123/edit/members');
  });

  it('does not show tabs if the members flag is disabled', () => {
    const header = createHeader({ group, enableMembers: false });
    assert.isTrue(getLink(header, 'activity-link').exists());
    assert.isFalse(getLink(header, 'settings-link').exists());
    assert.isFalse(getLink(header, 'members-link').exists());
  });

  it('should pass a11y checks', checkAccessibility({ content: createHeader }));
});
