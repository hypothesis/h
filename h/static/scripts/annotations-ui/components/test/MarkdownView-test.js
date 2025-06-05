import {
  checkAccessibility,
  mockImportedComponents,
  mount,
  waitFor,
} from '@hypothesis/frontend-testing';
import sinon from 'sinon';

import MarkdownView, { $imports } from '../MarkdownView';

describe('MarkdownView', () => {
  let fakeRenderMathAndMarkdown;
  let fakeReplaceLinksWithEmbeds;
  let fakeProcessAndReplaceMentionElements;
  let fakeClearTimeout;

  function createComponent(props = {}) {
    return mount(
      <MarkdownView
        markdown=""
        mentionMode="username"
        {...props}
        setTimeout_={callback => setTimeout(callback, 0)}
        clearTimeout_={fakeClearTimeout}
      />,
      { connected: true },
    );
  }

  function getMarkdownContainer(wrapper) {
    return wrapper.find('[data-testid="markdown-text"]');
  }

  beforeEach(() => {
    fakeRenderMathAndMarkdown = markdown => `rendered:${markdown}`;
    fakeReplaceLinksWithEmbeds = sinon.stub();
    fakeProcessAndReplaceMentionElements = sinon.stub();
    fakeClearTimeout = sinon.stub();

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '../utils': {
        renderMathAndMarkdown: fakeRenderMathAndMarkdown,
      },
      '../utils/media-embedder': {
        replaceLinksWithEmbeds: fakeReplaceLinksWithEmbeds,
      },
      '../helpers': {
        processAndReplaceMentionElements: fakeProcessAndReplaceMentionElements,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  it('renders nothing if no markdown is provided', () => {
    const wrapper = createComponent();
    assert.equal(wrapper.text(), '');
  });

  it('renders markdown as HTML', () => {
    const wrapper = createComponent({ markdown: '**test**' });
    const rendered = getMarkdownContainer(wrapper).getDOMNode();
    assert.equal(rendered.innerHTML, 'rendered:**test**');
  });

  it('re-renders markdown after an update', () => {
    const wrapper = createComponent({ markdown: '**test**' });
    wrapper.setProps({ markdown: '_updated_' });
    const rendered = getMarkdownContainer(wrapper).getDOMNode();
    assert.equal(rendered.innerHTML, 'rendered:_updated_');
  });

  it('replaces links with embeds in rendered output', () => {
    const wrapper = createComponent({ markdown: '**test**' });
    const rendered = getMarkdownContainer(wrapper).getDOMNode();
    assert.calledWith(fakeReplaceLinksWithEmbeds, rendered, {
      className: sinon.match.string,
    });
  });

  it('applies `textClass` class to container', () => {
    const wrapper = createComponent({
      markdown: 'foo',
      classes: 'fancy-effect',
    });
    assert.isTrue(wrapper.find('.fancy-effect').exists());
  });

  it('applies `textStyle` style to container', () => {
    const wrapper = createComponent({
      markdown: 'foo',
      style: { fontFamily: 'serif' },
    });
    assert.deepEqual(getMarkdownContainer(wrapper).prop('style'), {
      fontFamily: 'serif',
    });
  });

  [
    { mentions: undefined, mentionMode: 'username' },
    { mentions: [{}], mentionMode: 'display-name' },
  ].forEach(({ mentions, mentionMode }) => {
    it('renders mention tags based on provided mentions', () => {
      createComponent({ mentions, mentionMode });
      assert.calledWith(
        fakeProcessAndReplaceMentionElements,
        sinon.match.any,
        mentions ?? [],
        mentionMode,
      );
    });
  });

  context('when mentions are enabled', () => {
    let firstMentionElement;
    let firstMention;
    let secondMentionElement;
    let secondMention;
    let notMentionElement;

    function createComponentWithChildren() {
      const wrapper = createComponent({ mentionsEnabled: true });
      const markdownContainer = getMarkdownContainer(wrapper);
      markdownContainer
        .getDOMNode()
        .append(firstMentionElement, secondMentionElement, notMentionElement);

      return wrapper;
    }

    beforeEach(() => {
      firstMentionElement = document.createElement('a');
      firstMentionElement.textContent = 'first-mention';
      firstMention = {};

      secondMentionElement = document.createElement('span');
      secondMentionElement.textContent = 'second-mention';
      secondMention = 'invalid';

      notMentionElement = document.createElement('span');
      notMentionElement.textContent = 'not-a-mention';

      fakeProcessAndReplaceMentionElements.returns(
        new Map([
          [firstMentionElement, firstMention],
          [secondMentionElement, secondMention],
        ]),
      );

      // Add mentions to body so they have a non-zero area. This is needed
      // for testing handling of mouse events inside mentions.
      document.body.append(
        firstMentionElement,
        secondMentionElement,
        notMentionElement,
      );
    });

    afterEach(() => {
      firstMentionElement.remove();
      secondMentionElement.remove();
      notMentionElement.remove();
    });

    [true, false].forEach(mentionsEnabled => {
      it('renders Popover only if mentions are enabled', () => {
        const wrapper = createComponent({ mentionsEnabled });
        assert.equal(wrapper.exists('Popover'), mentionsEnabled);
      });
    });

    [
      {
        getElement: () => firstMentionElement,
        getExpectedMention: () => firstMention,
      },
      {
        getElement: () => secondMentionElement,
        getExpectedMention: () => secondMention,
      },
    ].forEach(({ getElement, getExpectedMention }) => {
      it('opens popover with expected content when hovering over mention element', async () => {
        const wrapper = createComponentWithChildren();

        getElement().dispatchEvent(new MouseEvent('mouseenter'));

        // The popover is "eventually" open after some delay
        await waitFor(() => {
          wrapper.update();
          return wrapper.find('Popover').prop('open');
        });
        assert.equal(
          wrapper.find('MentionPopoverContent').prop('content'),
          getExpectedMention(),
        );

        // Before the popover is visible, a "mouseleave" event on the anchor
        // will cause it not to be shown. After it becomes visible, a
        // "mouseleave" event will not hide the popover.
        getElement().dispatchEvent(new MouseEvent('mouseleave'));
        wrapper.update();
        assert.isTrue(wrapper.find('Popover').prop('open'));

        const moveMouse = (clientX, clientY) => {
          getElement().dispatchEvent(
            new MouseEvent('mousemove', {
              bubbles: true,
              clientX,
              clientY,
            }),
          );
          wrapper.update();
        };

        const anchorBox = getElement().getBoundingClientRect();
        const popoverBox = wrapper
          .find('[popover]')
          .getDOMNode()
          .getBoundingClientRect();

        // Move mouse inside anchor. Popover should remain open.
        moveMouse(anchorBox.x, anchorBox.y);
        assert.isTrue(wrapper.find('Popover').prop('open'));

        // Move mouse inside popover. Popover should remain open.
        moveMouse(popoverBox.x, popoverBox.y);
        assert.isTrue(wrapper.find('Popover').prop('open'));

        // Move mouse outside popover and anchor. The popover should be closed.
        moveMouse(popoverBox.x - 10, popoverBox.y);
        assert.isFalse(wrapper.find('Popover').prop('open'));
        assert.isFalse(wrapper.exists('MentionPopoverContent'));
      });
    });

    it('does not open popover when hovering over non-mention elements', () => {
      const wrapper = createComponentWithChildren();
      notMentionElement.dispatchEvent(new MouseEvent('mouseenter'));

      assert.isFalse(wrapper.find('Popover').prop('open'));
    });

    it('clears timeout when removing mouse from mention before popover is opened', () => {
      createComponentWithChildren();

      firstMentionElement.dispatchEvent(new MouseEvent('mouseenter'));
      firstMentionElement.dispatchEvent(new MouseEvent('mouseleave'));

      assert.called(fakeClearTimeout);
    });

    it('clears timeout when the component is unmounted', () => {
      const wrapper = createComponentWithChildren();

      firstMentionElement.dispatchEvent(new MouseEvent('mouseenter'));
      wrapper.unmount();

      assert.called(fakeClearTimeout);
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent({ markdown: 'foo' }),
    }),
  );
});
