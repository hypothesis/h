import { LinkButton } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { ComponentChildren } from 'preact';
import { useCallback, useLayoutEffect, useRef, useState } from 'preact/hooks';

import { observeElementSize } from '../util/observe-element-size';

type InlineControlsProps = {
  isCollapsed: boolean;
  setCollapsed: (collapsed: boolean) => void;
};

/**
 * An optional toggle link at the bottom of an excerpt which controls whether
 * it is expanded or collapsed.
 */
function InlineControls({ isCollapsed, setCollapsed }: InlineControlsProps) {
  return (
    <div
      className={classnames(
        // Position these controls at the bottom right of the excerpt
        'absolute block right-0 bottom-0',
        // Give extra width for larger tap target and gradient fade
        // Fade transparent-to-white left-to-right to make the toggle
        // control text (More/Less) more readable above other text.
        // This gradient is implemented to-left to take advantage of Tailwind's
        // automatic to-transparent calculation: this avoids Safari's problem
        // with transparents in gradients:
        // https://bugs.webkit.org/show_bug.cgi?id=150940
        // https://tailwindcss.com/docs/gradient-color-stops#fading-to-transparent
        'w-20 bg-gradient-to-l from-white',
      )}
    >
      <div className="flex justify-end">
        <LinkButton
          variant="text"
          onClick={() => setCollapsed(!isCollapsed)}
          expanded={!isCollapsed}
          title="Toggle visibility of full excerpt text"
          underline="always"
          inline
        >
          {isCollapsed ? 'More' : 'Less'}
        </LinkButton>
      </div>
    </div>
  );
}

const noop = () => {};

type ExcerptProps = {
  children?: ComponentChildren;
  /**
   * If `true`, the excerpt provides internal controls to expand and collapse
   * the content. If `false`, the caller sets the collapsed state via the
   * `collapse` prop.  When using inline controls, the excerpt is initially
   * collapsed.
   */
  inlineControls?: boolean;
  /**
   * If the content should be truncated if its height exceeds
   * `collapsedHeight + overflowThreshold`. This prop is only used if
   * `inlineControls` is false.
   */
  collapse?: boolean;
  /**
   * Maximum height of the container, in pixels, when it is collapsed.
   */
  collapsedHeight: number;
  /**
   * An additional margin of pixels by which the content height can exceed
   * `collapsedHeight` before it becomes collapsible.
   */
  overflowThreshold?: number;
  /**
   * Called when the content height exceeds or falls below
   * `collapsedHeight + overflowThreshold`.
   */
  onCollapsibleChanged?: (isCollapsible: boolean) => void;
  /**
   * When `inlineControls` is `false`, this function is called when the user
   * requests to expand the content by clicking a zone at the bottom of the
   * container.
   */
  onToggleCollapsed?: (collapsed: boolean) => void;
};

/**
 * A container which truncates its content when they exceed a specified height.
 *
 * The collapsed state of the container can be handled either via internal
 * controls (if `inlineControls` is `true`) or by the caller using the
 * `collapse` prop.
 */
export default function Excerpt({
  children,
  collapse = false,
  collapsedHeight,
  inlineControls = true,
  onCollapsibleChanged = noop,
  onToggleCollapsed = noop,
  overflowThreshold = 0,
}: ExcerptProps) {
  const [collapsedByInlineControls, setCollapsedByInlineControls] =
    useState(true);

  const contentElement = useRef<HTMLDivElement | null>(null);

  // Measured height of `contentElement` in pixels
  const [contentHeight, setContentHeight] = useState(0);

  // Update the measured height of the content container after initial render,
  // and when the size of the content element changes.
  const updateContentHeight = useCallback(() => {
    const newContentHeight = contentElement.current!.clientHeight;
    setContentHeight(newContentHeight);

    // prettier-ignore
    const isCollapsible =
      newContentHeight > (collapsedHeight + overflowThreshold);
    onCollapsibleChanged(isCollapsible);
  }, [collapsedHeight, onCollapsibleChanged, overflowThreshold]);

  useLayoutEffect(() => {
    const cleanup = observeElementSize(
      contentElement.current!,
      updateContentHeight,
    );
    updateContentHeight();
    return cleanup;
  }, [updateContentHeight]);

  // Render the (possibly truncated) content and controls for
  // expanding/collapsing the content.
  // prettier-ignore
  const isOverflowing = contentHeight > (collapsedHeight + overflowThreshold);
  const isCollapsed = inlineControls ? collapsedByInlineControls : collapse;
  const isExpandable = isOverflowing && isCollapsed;

  const contentStyle: Record<string, number> = {};
  if (contentHeight !== 0) {
    contentStyle['max-height'] = isExpandable ? collapsedHeight : contentHeight;
  }

  const setCollapsed = (collapsed: boolean) =>
    inlineControls
      ? setCollapsedByInlineControls(collapsed)
      : onToggleCollapsed(collapsed);

  return (
    <div
      data-testid="excerpt-container"
      className={classnames(
        'relative overflow-hidden',
        'transition-[max-height] ease-in duration-150',
      )}
      style={contentStyle}
    >
      <div
        className={classnames(
          // Establish new block-formatting context to prevent margin-collapsing
          // in descendent elements from potentially "leaking out" and pushing
          // this element down from the top of the container.
          // See https://developer.mozilla.org/en-US/docs/Web/Guide/CSS/Block_formatting_context
          // See https://github.com/hypothesis/client/issues/1518
          'inline-block w-full',
        )}
        data-testid="excerpt-content"
        ref={contentElement}
      >
        {children}
      </div>
      <div
        data-testid="excerpt-expand"
        role="presentation"
        onClick={() => setCollapsed(false)}
        className={classnames(
          // This element provides a clickable area at the bottom of an
          // expandable excerpt to expand it.
          'transition-[opacity] duration-150 ease-linear',
          'absolute w-full bottom-0 h-touch-minimum',
          {
            // For expandable excerpts not using inlineControls, style this
            // element with a custom shadow-like gradient
            'bg-gradient-to-b from-excerpt-stop-1 via-excerpt-stop-2 to-excerpt-stop-3':
              !inlineControls && isExpandable,
            'bg-none': inlineControls,
            // Don't make this shadow visible OR clickable if there's nothing
            // to do here (the excerpt isn't expandable)
            'opacity-0 pointer-events-none': !isExpandable,
          },
        )}
        title="Show the full excerpt"
      />
      {isOverflowing && inlineControls && (
        <InlineControls
          isCollapsed={collapsedByInlineControls}
          setCollapsed={setCollapsed}
        />
      )}
    </div>
  );
}
