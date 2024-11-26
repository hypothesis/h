import { mount } from '@hypothesis/frontend-testing';
import { Link } from 'wouter-preact';
import { act } from 'preact/test-utils';

import { $imports, default as Router } from '../Router';

function App() {
  return (
    <Router>
      <Link data-testid="link" href="/test/path">
        Test link
      </Link>
    </Router>
  );
}

describe('Router', () => {
  let fakeHasUnsavedChanges;
  let initialHistoryLen;

  beforeEach(() => {
    fakeHasUnsavedChanges = sinon.stub().returns(false);
    initialHistoryLen = history.length;

    $imports.$mock({
      '../utils/unsaved-changes': {
        hasUnsavedChanges: fakeHasUnsavedChanges,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();

    const backSteps = history.length - initialHistoryLen;
    if (backSteps > 0) {
      history.go(-backSteps);
    }
  });

  function clickLink(wrapper) {
    act(() => {
      wrapper.find('a').getDOMNode().click();
    });
    wrapper.update();
  }

  it('navigates without warning if there are no unsaved changes', () => {
    const wrapper = mount(<App />);
    clickLink(wrapper);
    assert.isFalse(wrapper.exists('WarningDialog'));
    assert.equal(location.pathname, '/test/path');
  });

  it('shows a warning if there are unsaved changes', () => {
    // Click link when there are unsaved changes.
    history.pushState({}, '', '/original/url');
    fakeHasUnsavedChanges.returns(true);
    const wrapper = mount(<App />);
    clickLink(wrapper);

    // The confirmation dialog should be shown.
    const warning = wrapper.find('WarningDialog');
    assert.isTrue(warning.exists());
    assert.notEqual(location.pathname, '/test/path');

    // Canceling the dialog should leave the location unchanged
    warning.prop('onCancel')();
    wrapper.update();
    assert.isFalse(wrapper.exists('WarningDialog'));
    assert.notEqual(location.pathname, '/test/path');

    // Click the link again, but this time confirm the navigation.
    clickLink(wrapper);
    const warning2 = wrapper.find('WarningDialog');
    warning2.prop('onConfirm')();
    wrapper.update();

    assert.isFalse(wrapper.exists('WarningDialog'));
    assert.equal(location.pathname, '/test/path');
  });
});
