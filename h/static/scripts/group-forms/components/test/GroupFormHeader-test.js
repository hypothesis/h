import { checkAccessibility, mount } from '@hypothesis/frontend-testing';

import { Config } from '../../config';
import GroupFormHeader from '../GroupFormHeader';

describe('GroupFormHeader', () => {
  let config;

  beforeEach(() => {
    config = {
      features: {
        group_members: true,
        group_moderation: true,
      },
    };
  });

  const createHeader = (props = {}) =>
    mount(
      <Config.Provider value={config}>
        <GroupFormHeader {...props} />
      </Config.Provider>,
    );

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
    assert.isFalse(getLink(header, 'moderation-link').exists());
  });

  it('renders group activity link and tabs if there is a group', () => {
    const header = createHeader({ group });

    const activityLink = getLink(header, 'activity-link');
    assert.equal(activityLink.prop('href'), group.link);

    const settingsLink = getLink(header, 'settings-link');
    assert.equal(settingsLink.prop('href'), '/groups/abc123/edit');

    const membersLink = getLink(header, 'members-link');
    assert.equal(membersLink.prop('href'), '/groups/abc123/edit/members');

    const moderationLink = getLink(header, 'moderation-link');
    assert.equal(moderationLink.prop('href'), '/groups/abc123/moderate');
  });

  it('does not show tabs if the members flag is disabled', () => {
    config.features.group_members = false;
    const header = createHeader({ group });
    assert.isTrue(getLink(header, 'activity-link').exists());
    assert.isFalse(getLink(header, 'settings-link').exists());
    assert.isFalse(getLink(header, 'members-link').exists());
  });

  it('does not show moderation link if the moderation flag is disabled', () => {
    config.features.group_moderation = false;
    const header = createHeader({ group });
    assert.isFalse(getLink(header, 'moderation-link').exists());
  });

  it('should pass a11y checks', checkAccessibility({ content: createHeader }));
});
