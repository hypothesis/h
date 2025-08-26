import { checkAccessibility, mount } from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';
import { Router } from 'wouter-preact';

import TabLinks from '../TabLinks';

describe('TabLinks', () => {
  const createWrapper = (initialLocation = '/') => {
    // Set initial location. We currently modify the real URL, but could mock
    // `useRoute` if that becomes problematic.
    history.pushState({}, '', initialLocation);

    return mount(
      <Router>
        <TabLinks>
          <TabLinks.Link href="/profile" testId="profile-tab">
            Profile
          </TabLinks.Link>
          <TabLinks.Link href="/notifications" testId="notifications-tab">
            Notifications
          </TabLinks.Link>
        </TabLinks>
      </Router>,
    );
  };

  const getTab = (wrapper, testId) => {
    // We use `first()` here to get the outermost component of the link.
    return wrapper.find(`[data-testid="${testId}"]`).first();
  };

  afterEach(() => {
    // Reset to initial location
    history.pushState({}, '', '/');
  });

  it('displays tab for current route as selected', () => {
    const wrapper = createWrapper('/profile');

    let profileTab = getTab(wrapper, 'profile-tab');
    let notificationsTab = getTab(wrapper, 'notifications-tab');

    assert.isTrue(profileTab.prop('aria-current'));
    assert.isFalse(notificationsTab.prop('aria-current'));

    act(() => {
      history.pushState({}, '', '/notifications');
    });
    wrapper.update();

    profileTab = getTab(wrapper, 'profile-tab');
    notificationsTab = getTab(wrapper, 'notifications-tab');

    assert.isTrue(notificationsTab.prop('aria-current'));
    assert.isFalse(profileTab.prop('aria-current'));
  });

  it('renders client-side router links by default', () => {
    const wrapper = createWrapper();
    const profileTab = getTab(wrapper, 'profile-tab');

    // Should render as a router Link component (not a plain 'a' tag)
    assert.notEqual(profileTab.name(), 'a');
  });

  it('renders server-side links when `server` prop is true', () => {
    const wrapper = mount(
      <Router>
        <TabLinks>
          <TabLinks.Link href="/external" server testId="external-tab">
            External Link
          </TabLinks.Link>
        </TabLinks>
      </Router>,
    );

    const externalTab = getTab(wrapper, 'external-tab');
    assert.equal(externalTab.name(), 'a');
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: () => createWrapper() }),
  );
});
