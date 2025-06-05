import { Popover } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from 'preact/hooks';

import MentionPopoverContent from '../components/MentionPopoverContent';
import StyledText from '../components/StyledText';
import { processAndReplaceMentionElements } from '../helpers';
import type {
  InvalidMentionContent,
  MentionMode,
  Mention,
} from '../helpers/mentions';
import { renderMathAndMarkdown } from '../utils';
import { replaceLinksWithEmbeds } from '../utils/media-embedder';

/** Return true if the point (x, y) lies within `rect`. */
function rectContainsPoint(rect: DOMRect, x: number, y: number): boolean {
  return x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom;
}

/**
 * Return the smallest rect that entirely contains `rect` and has integer
 * coordinates.
 */
function roundRectCoords(rect: DOMRect): DOMRect {
  const left = Math.floor(rect.x);
  const top = Math.floor(rect.y);
  const right = Math.ceil(rect.right);
  const bottom = Math.ceil(rect.bottom);
  return new DOMRect(left, top, right - left, bottom - top);
}

/** Return the smallest rect which contains both `a` and `b`. */
function unionRect(a: DOMRect, b: DOMRect): DOMRect {
  const left = Math.min(a.x, b.x);
  const top = Math.min(a.y, b.y);
  const right = Math.max(a.right, b.right);
  const bottom = Math.max(a.bottom, b.bottom);

  return DOMRect.fromRect({
    x: left,
    y: top,
    width: right - left,
    height: bottom - top,
  });
}

export type MarkdownViewProps = {
  /** The string of markdown to display as HTML. */
  markdown: string;
  classes?: string;
  style?: Record<string, string>;
  mentions?: Mention[];
  mentionMode: MentionMode;

  /**
   * Whether the at-mentions feature ir enabled or not.
   * Defaults to false.
   */
  mentionsEnabled?: boolean;

  // Test seams
  setTimeout_?: typeof setTimeout;
  clearTimeout_?: typeof clearTimeout;
};

type PopoverContent = Mention | InvalidMentionContent | null;

/**
 * A component which renders markdown as HTML, replaces recognized links with
 * embedded video/audio and processes mention tags.
 */
export default function MarkdownView(props: MarkdownViewProps) {
  /* istanbul ignore next - Unpack here to ignore default values for test seams */
  const {
    markdown,
    classes,
    style,
    mentions = [],
    mentionsEnabled = false,
    mentionMode,
    setTimeout_ = setTimeout,
    clearTimeout_ = clearTimeout,
  } = props;
  const html = useMemo(
    () => (markdown ? renderMathAndMarkdown(markdown) : ''),
    [markdown],
  );
  const content = useRef<HTMLDivElement | null>(null);

  const mentionsPopoverAnchorRef = useRef<HTMLElement | null>(null);
  const mentionsPopoverRef = useRef<HTMLElement>(null);

  const elementToMentionMap = useRef(
    new Map<HTMLElement, Mention | InvalidMentionContent>(),
  );
  const [popoverContent, setPopoverContent] = useState<PopoverContent>(null);
  const popoverContentTimeout = useRef<ReturnType<typeof setTimeout> | null>();
  const setPopoverContentAfterDelay = useCallback(
    // This allows the content to be set with a small delay, so that popovers
    // don't flicker simply by hovering an annotation with mentions
    (content: PopoverContent) => {
      if (popoverContentTimeout.current) {
        clearTimeout_(popoverContentTimeout.current);
      }

      const setContent = () => {
        setPopoverContent(content);
        popoverContentTimeout.current = null;
      };

      // Set the content immediately when resetting, so that there's no delay
      // when hiding the popover, only when showing it
      if (content === null) {
        setContent();
      } else {
        popoverContentTimeout.current = setTimeout_(setContent, 400);
      }
    },
    [clearTimeout_, setTimeout_],
  );

  useEffect(() => {
    // Clear any potentially in-progress popover timeout when this component is
    // unmounted
    return () => {
      if (popoverContentTimeout.current) {
        clearTimeout_(popoverContentTimeout.current);
      }
    };
  }, [clearTimeout_]);

  useEffect(() => {
    replaceLinksWithEmbeds(content.current!, {
      // Make embeds the full width of the sidebar, unless the sidebar has been
      // made wider than the `md` breakpoint. In that case, restrict width
      // to 380px.
      className: 'w-full md:w-[380px]',
    });
  }, [markdown]);

  useEffect(() => {
    elementToMentionMap.current = processAndReplaceMentionElements(
      content.current!,
      mentions,
      mentionMode,
    );
  }, [mentionMode, mentions]);

  // Monitor mouse position when mentions popover is visible and hide when it
  // goes outside the anchor or popover.
  useLayoutEffect(() => {
    const anchor = mentionsPopoverAnchorRef.current;
    const popover = mentionsPopoverRef.current;
    if (!anchor || !popover || !popoverContent) {
      return () => {};
    }

    const maybeHidePopover = (e: MouseEvent) => {
      // Element boxes may have fractional coordinates, but mouse event
      // coordinates are integers (in Chrome at least). Expand the boxes to the
      // smallest box with integer coordinates. This way a mouse event
      // dispatched at the exact corner of one of the boxes will still be deemed
      // "inside".
      const anchorBox = roundRectCoords(anchor.getBoundingClientRect());
      const popoverBox = roundRectCoords(popover.getBoundingClientRect());

      // There may be a small gap between the anchor and popover. To avoid
      // hiding the popover when the mouse moves across this gap, we only hide
      // the popover when it moves outside the union of these two boxes.
      const unionBox = unionRect(anchorBox, popoverBox);

      if (!rectContainsPoint(unionBox, e.clientX, e.clientY)) {
        setPopoverContentAfterDelay(null);
        mentionsPopoverAnchorRef.current = null;
      }
    };

    // Use a listener on the body because there isn't a single element that
    // corresponds to the region which the mouse has to exit before we hide the
    // popover.
    document.body.addEventListener('mousemove', maybeHidePopover);
    return () => {
      document.body.removeEventListener('mousemove', maybeHidePopover);
    };
  }, [popoverContent, setPopoverContentAfterDelay]);

  // NB: The following could be implemented by setting attribute props directly
  // on `StyledText` (which renders a `div` itself), versus introducing a child
  // `div` as is done here. However, in initial testing, this interfered with
  // some overflow calculations in the `Excerpt` element. This could be worth
  // a review in the future.
  return (
    <div
      className={classnames('w-full break-anywhere cursor-text', {
        // A `relative` wrapper around the `Popover` component is needed for
        // when the native Popover API is not supported.
        relative: mentionsEnabled,
      })}
    >
      <StyledText>
        <div
          className={classes}
          data-testid="markdown-text"
          ref={content}
          dangerouslySetInnerHTML={{ __html: html }}
          style={style}
          onMouseEnterCapture={
            mentionsEnabled
              ? ({ target }) => {
                  const element = target as HTMLElement;
                  const mention = elementToMentionMap.current.get(element);

                  if (mention) {
                    setPopoverContentAfterDelay(mention);
                    mentionsPopoverAnchorRef.current = element;
                  }
                }
              : undefined
          }
          onMouseLeaveCapture={({ target }) => {
            // If the mouse leaves the mention before the popover has been
            // shown, cancel the timer that shows the popover.
            //
            // Once the popover is shown, hiding it is handled by a separate
            // effect that fires once the mouse leaves the area containing both
            // the popover and the anchor.
            const element = target as HTMLElement;
            if (
              mentionsPopoverAnchorRef.current === element &&
              !popoverContent
            ) {
              setPopoverContentAfterDelay(null);
              mentionsPopoverAnchorRef.current = null;
            }
          }}
        />
      </StyledText>
      {mentionsEnabled && (
        <Popover
          open={!!popoverContent}
          onClose={() => setPopoverContentAfterDelay(null)}
          anchorElementRef={mentionsPopoverAnchorRef}
          classes="!max-w-[75%]"
          elementRef={mentionsPopoverRef}
        >
          {popoverContent !== null && (
            <MentionPopoverContent
              content={popoverContent}
              mentionMode={mentionMode}
            />
          )}
        </Popover>
      )}
    </div>
  );
}
