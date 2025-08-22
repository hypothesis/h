import { checkAccessibility, mount } from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';

import CopyButton from '../CopyButton';

describe('CopyButton', () => {
  let clock;
  let fakeClipboard;

  beforeEach(() => {
    fakeClipboard = {
      writeText: sinon.stub().resolves(),
    };
    sinon.stub(navigator, 'clipboard').value(fakeClipboard);
    clock = sinon.useFakeTimers();
  });

  afterEach(() => {
    clock.restore();
    sinon.restore();
  });

  function createComponent(props = {}) {
    return mount(
      <CopyButton title="Copy text" value="text to copy" {...props} />,
    );
  }

  it('renders copy icon initially', () => {
    const wrapper = createComponent();
    const button = wrapper.find('IconButton');

    assert.equal(button.prop('title'), 'Copy text');
    assert.equal(button.prop('icon').name, 'CopyIcon');
  });

  it('copies text to clipboard when clicked', async () => {
    const wrapper = createComponent({ value: 'test text' });

    await act(async () => {
      wrapper.find('IconButton').prop('onClick')();
    });

    assert.calledWith(fakeClipboard.writeText, 'test text');
  });

  it('shows check icon after copying', async () => {
    const wrapper = createComponent();

    await act(async () => {
      wrapper.find('IconButton').prop('onClick')();
    });

    wrapper.update();
    assert.equal(wrapper.find('IconButton').prop('icon').name, 'CheckIcon');
  });

  it('reverts to copy icon after timeout', async () => {
    const wrapper = createComponent();

    await act(async () => {
      wrapper.find('IconButton').prop('onClick')();
    });

    wrapper.update();
    assert.equal(wrapper.find('IconButton').prop('icon').name, 'CheckIcon');

    act(() => {
      clock.tick(1000);
    });

    wrapper.update();
    assert.equal(wrapper.find('IconButton').prop('icon').name, 'CopyIcon');
  });

  it('does not revert to copy icon if timeout is cleared', async () => {
    const wrapper = createComponent();

    await act(async () => {
      wrapper.find('IconButton').prop('onClick')();
    });

    wrapper.update();
    assert.equal(wrapper.find('IconButton').prop('icon').name, 'CheckIcon');

    // Unmount component to trigger cleanup
    wrapper.unmount();

    act(() => {
      clock.tick(1000);
    });

    // No assertion needed - this test ensures no errors occur when
    // timeout cleanup happens after component unmount
  });

  it('handles multiple clicks correctly', async () => {
    const wrapper = createComponent({ value: 'test' });

    // First click
    await act(async () => {
      wrapper.find('IconButton').prop('onClick')();
    });

    wrapper.update();
    assert.equal(wrapper.find('IconButton').prop('icon').name, 'CheckIcon');
    assert.calledWith(fakeClipboard.writeText, 'test');

    // Second click before timeout
    act(() => {
      clock.tick(500);
    });

    await act(async () => {
      wrapper.find('IconButton').prop('onClick')();
    });

    assert.calledTwice(fakeClipboard.writeText);

    // Icon should still be CheckIcon and timeout should reset
    wrapper.update();
    assert.equal(wrapper.find('IconButton').prop('icon').name, 'CheckIcon');

    act(() => {
      clock.tick(1000);
    });

    wrapper.update();
    assert.equal(wrapper.find('IconButton').prop('icon').name, 'CopyIcon');
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => {
        clock.restore();
        return createComponent();
      },
    }),
  );
});
