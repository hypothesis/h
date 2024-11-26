import { mount } from '@hypothesis/frontend-testing';
import { useUnsavedChanges, hasUnsavedChanges } from '../unsaved-changes';

function TestUseUnsavedChanges({ unsaved, fakeWindow }) {
  useUnsavedChanges(unsaved, fakeWindow);
  return <div />;
}

describe('useUnsavedChanges', () => {
  let fakeWindow;

  function dispatchBeforeUnload() {
    const event = new Event('beforeunload', { cancelable: true });
    fakeWindow.dispatchEvent(event);
    return event;
  }

  function createWidget(unsaved) {
    return mount(
      <TestUseUnsavedChanges fakeWindow={fakeWindow} unsaved={unsaved} />,
    );
  }

  beforeEach(() => {
    // Use a dummy window to avoid triggering any handlers that respond to
    // "beforeunload" on the real window.
    fakeWindow = new EventTarget();
  });

  it('does not increment unsaved-changes count if argument is false', () => {
    createWidget(false);
    assert.isFalse(hasUnsavedChanges());
  });

  it('does not register "beforeunload" handler if argument is false', () => {
    createWidget(false);
    const event = dispatchBeforeUnload();
    assert.isFalse(event.defaultPrevented);
  });

  it('increments unsaved-changes count if argument is true', () => {
    const wrapper = createWidget(true);
    assert.isTrue(hasUnsavedChanges());
    wrapper.unmount();
    assert.isFalse(hasUnsavedChanges());
  });

  it('registers "beforeunload" handler if argument is true', () => {
    const wrapper = createWidget(true);
    const event = dispatchBeforeUnload();
    assert.isTrue(event.defaultPrevented);

    // Unmount the widget, this should remove the handler.
    wrapper.unmount();
    const event2 = dispatchBeforeUnload();
    assert.isFalse(event2.defaultPrevented);
  });
});
