import { formatDateTime } from '@hypothesis/frontend-shared';
import { checkAccessibility, mount } from '@hypothesis/frontend-testing';

import MentionPopoverContent from '../MentionPopoverContent';

describe('MentionPopoverContent', () => {
  function createComponent(content, mentionMode = 'username') {
    return mount(
      <MentionPopoverContent content={content} mentionMode={mentionMode} />,
    );
  }

  it('renders user-not-found message when InvalidUser is provided', () => {
    const wrapper = createComponent('@invalid');
    const userNotFound = wrapper.find('[data-testid="user-not-found"]');

    assert.isTrue(userNotFound.exists());
    assert.equal('No user with username @invalid exists', userNotFound.text());
    assert.isFalse(wrapper.exists('[data-testid="username"]'));
    assert.isFalse(wrapper.exists('[data-testid="display-name"]'));
  });

  it('renders no display name nor description when not provided', () => {
    const wrapper = createComponent({ username: 'janedoe' });

    assert.equal(wrapper.find('[data-testid="username"]').text(), '@janedoe');
    assert.isFalse(wrapper.exists('[data-testid="display-name"]'));
    assert.isFalse(wrapper.exists('[data-testid="description"]'));
  });

  it('renders display name when provided', () => {
    const wrapper = createComponent({
      username: 'janedoe',
      display_name: 'Jane Doe',
    });

    assert.equal(wrapper.find('[data-testid="username"]').text(), '@janedoe');
    assert.equal(
      wrapper.find('[data-testid="display-name"]').text(),
      'Jane Doe',
    );
    assert.isFalse(wrapper.exists('[data-testid="description"]'));
  });

  it('renders description when provided', () => {
    const wrapper = createComponent({
      username: 'janedoe',
      description: 'This is my bio',
    });

    assert.equal(wrapper.find('[data-testid="username"]').text(), '@janedoe');
    assert.isFalse(wrapper.exists('[data-testid="display-name"]'));
    assert.equal(
      wrapper.find('[data-testid="description"]').text(),
      'This is my bio',
    );
  });

  it('renders both display name and description when provided', () => {
    const wrapper = createComponent({
      username: 'janedoe',
      display_name: 'Jane Doe',
      description: 'This is my bio',
    });

    assert.equal(wrapper.find('[data-testid="username"]').text(), '@janedoe');
    assert.equal(
      wrapper.find('[data-testid="display-name"]').text(),
      'Jane Doe',
    );
    assert.equal(
      wrapper.find('[data-testid="description"]').text(),
      'This is my bio',
    );
  });

  [
    { joined: null, shouldRenderJoinedDate: false },
    {
      joined: '2008-02-29T13:00:00.000000+00:00',
      shouldRenderJoinedDate: true,
    },
  ].forEach(({ joined, shouldRenderJoinedDate }) => {
    it('shows join date only if set', () => {
      const wrapper = createComponent({ username: 'janedoe', joined });
      assert.equal(
        wrapper.exists('[data-testid="joined"]'),
        shouldRenderJoinedDate,
      );
    });
  });

  [
    '2025-01-23T15:36:52.100817+00:00',
    '2022-08-16T00:00:00.000000+00:00',
    '2008-02-29T13:00:00.000000+00:00',
  ].forEach(joined => {
    it('formats created date', () => {
      const wrapper = createComponent({ username: 'janedoe', joined });
      assert.equal(
        wrapper.find('[data-testid="joined"]').text(),
        `Joined ${formatDateTime(joined, { includeTime: false })}`,
      );
    });
  });

  it('does not render username in display-name mode', () => {
    const wrapper = createComponent(
      { username: 'janedoe', display_name: 'Jane Doe' },
      'display-name',
    );

    assert.equal(
      wrapper.find('[data-testid="display-name"]').text(),
      'Jane Doe',
    );
    assert.isFalse(wrapper.exists('[data-testid="username"]'));
  });

  [
    {
      mentionMode: 'username',
      expectedLink:
        'https://web.hypothes.is/help/mentions-for-the-hypothesis-web-app/',
    },
    {
      mentionMode: 'display-name',
      expectedLink:
        'https://web.hypothes.is/help/mentions-for-the-hypothesis-lms-app/',
    },
  ].forEach(({ mentionMode, expectedLink }) => {
    it('adds different KB article link depending on mention mode', () => {
      const wrapper = createComponent({ username: 'janedoe' }, mentionMode);
      const link = wrapper.find('Link[data-testid="kb-article-link"]');

      assert.equal(link.prop('href'), expectedLink);
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility([
      {
        name: 'Invalid mention',
        content: () => createComponent('invalid'),
      },
      {
        name: 'Valid mention',
        content: () =>
          createComponent({
            username: 'janedoe',
            display_name: 'Jane Doe',
            description: 'This is my bio',
            created: '2025-01-23T15:36:52.100817+00:00',
          }),
      },
    ]),
  );
});
