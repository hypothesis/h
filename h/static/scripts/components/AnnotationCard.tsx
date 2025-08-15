import {
  AnnotationGroupInfo,
  AnnotationShareControl,
  AnnotationTimestamps,
  AnnotationUser,
  Excerpt,
  ModerationStatusSelect,
  StyledText,
} from '@hypothesis/annotation-ui';
import {
  Callout,
  Card,
  CardContent,
  ExternalIcon,
  Link,
  ReplyIcon,
  lazy,
  Button,
  ExpandIcon,
  CollapseIcon,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useCallback, useContext, useMemo, useState } from 'preact/hooks';

import { GroupFormsConfig } from '../config';
import { useUpdateModerationStatus } from '../hooks/use-update-moderation-status';
import { quote, username as getUsername } from '../util/annotation-metadata';
import type { APIAnnotationData, ModerationStatus } from '../util/api';
import { callAPI } from '../util/api';
import { APIError } from '../util/api';
import AnnotationDocument from './AnnotationDocument';

export type AnnotationCardProps = {
  annotation: APIAnnotationData;

  /**
   * Invoked after successfully changing the moderation status for this
   * annotation
   */
  onStatusChange: (moderationStatus: ModerationStatus) => void;

  /**
   * Invoked when the annotation is reloaded, with the new annotation data
   */
  onAnnotationReloaded: (newAnnotationData: APIAnnotationData) => void;
};

type SaveState =
  | { type: 'saved' }
  | { type: 'saving' }
  | { type: 'error'; message: string }
  | { type: 'warning'; message: string };

// Lazily load the MarkdownView as it has heavy dependencies such as Showdown,
// KaTeX and DOMPurify.
const MarkdownView = lazy('MarkdownView', () => import('./MarkdownView'), {
  fallback: ({ markdown }) => markdown,
  errorFallback: /* istanbul ignore next */ ({ markdown }) => markdown,
});

export default function AnnotationCard({
  annotation,
  onStatusChange,
  onAnnotationReloaded,
}: AnnotationCardProps) {
  const config = useContext(GroupFormsConfig)!;
  const username = getUsername(annotation.user);
  const user =
    annotation.user_info?.display_name ?? username ?? annotation.user;
  const group = useMemo(
    () =>
      config.context.group && {
        type: config.context.group.type,
        name: config.context.group.name,
        links: {
          html: config.context.group.link,
        },
      },
    [config.context.group],
  );
  const isReply = (annotation.references ?? []).length > 0;
  const reloadAnnotation = useCallback(async () => {
    const { url: urlTemplate, ...rest } = config.api.annotationDetail!;
    const newAnnotationData = await callAPI<APIAnnotationData>(
      urlTemplate.replace(':annotationId', annotation.id),
      rest,
    );

    onAnnotationReloaded(newAnnotationData);
  }, [annotation, config.api?.annotationDetail, onAnnotationReloaded]);

  const updateModerationStatus = useUpdateModerationStatus(annotation);
  const [moderationSaveState, setModerationSaveState] = useState<SaveState>({
    type: 'saved',
  });
  const onModerationStatusChange = useCallback(
    async (status: ModerationStatus) => {
      try {
        setModerationSaveState({ type: 'saving' });
        await updateModerationStatus(status);
        onStatusChange(status);
        setModerationSaveState({ type: 'saved' });
      } catch (e) {
        const isConflictError =
          e instanceof APIError && e.response?.status === 409;
        let message = isConflictError
          ? 'The annotation has been updated since this page was loaded. Review this new version and try again.'
          : 'An error occurred updating the moderation status.';
        let type: 'warning' | 'error' = isConflictError ? 'warning' : 'error';

        // If there was a conflict, reload the annotation before reporting the
        // error
        if (isConflictError) {
          await reloadAnnotation().catch(() => {
            // If reloading the annotation fails, the error message should not
            // make users think they are seeing up-to-date information
            message =
              'The annotation has been updated since this page was loaded.';
            type = 'error';
          });
        }

        setModerationSaveState({ type, message });
      }
    },
    [onStatusChange, reloadAnnotation, updateModerationStatus],
  );

  const userLink = username
    ? config.routes['activity.user_search'].replace(':username', username)
    : undefined;

  const annoQuote = quote(annotation);

  // Should the annotation body be rendered in a collapsed state, assuming it is
  // collapsible (exceeds allotted collapsed space)?
  const [bodyCollapsed, setBodyCollapsed] = useState(true);
  // Does the annotation body take up enough vertical space that
  // collapsing/expanding is relevant?
  const [bodyCollapsible, setBodyCollapsible] = useState(false);

  return useMemo(
    () => (
      <article>
        <Card
          classes={classnames({
            'border-red': annotation.moderation_status === 'DENIED',
            'border-yellow': annotation.moderation_status === 'SPAM',
            'border-green': annotation.moderation_status === 'APPROVED',
          })}
        >
          <CardContent>
            <header className="w-full">
              <div className="flex gap-x-1 items-center justify-between">
                <AnnotationUser displayName={user} authorLink={userLink} />
                <AnnotationTimestamps
                  annotationCreated={annotation.created}
                  annotationUpdated={annotation.updated}
                  withEditedTimestamp={
                    annotation.updated !== annotation.created
                  }
                />
              </div>
              <div className="flex gap-x-1 items-baseline flex-wrap-reverse">
                {group && (
                  <>
                    <AnnotationGroupInfo group={group} />
                    <AnnotationDocument annotation={annotation} />
                  </>
                )}
                {isReply && (
                  <div
                    className="ml-auto flex items-center gap-x-1"
                    data-testid="reply-indicator"
                  >
                    <ReplyIcon /> This is a reply
                  </div>
                )}
              </div>
            </header>

            {annoQuote && (
              <Excerpt
                inlineControl
                collapsedHeight={40}
                overflowThreshold={20}
              >
                <StyledText>
                  <blockquote className="hover:border-l-blue-quote">
                    {annoQuote}
                  </blockquote>
                </StyledText>
              </Excerpt>
            )}

            <Excerpt
              inlineControl={false}
              collapsedHeight={194}
              overflowThreshold={20}
              collapsed={bodyCollapsed}
              onToggleCollapsed={setBodyCollapsed}
              onCollapsibleChanged={setBodyCollapsible}
              data-testid="anno-body-excerpt"
            >
              <MarkdownView
                markdown={annotation.text}
                mentions={annotation.mentions}
                mentionMode="username"
                mentionsEnabled
                classes="text-color-text hyp-wrap-anywhere"
              />
            </Excerpt>
            {bodyCollapsible && (
              <div className="flex justify-end !mt-1">
                <Button
                  classes="font-normal"
                  onClick={() => setBodyCollapsed(prev => !prev)}
                  data-testid="toggle-anno-body"
                  expanded={!bodyCollapsed}
                >
                  {bodyCollapsed ? <ExpandIcon /> : <CollapseIcon />}
                  Show {bodyCollapsed ? 'more' : 'less'}
                </Button>
              </div>
            )}

            {annotation.tags.length > 0 && (
              <ul
                className="flex flex-wrap gap-1 text-sm"
                data-testid="tags-container"
              >
                {annotation.tags.map(tag => (
                  <li
                    key={tag}
                    className={classnames(
                      'px-1.5 py-0.5 rounded text-color-text-light',
                      'border border-solid border-grey-3 bg-grey-0',
                    )}
                  >
                    {tag}
                  </li>
                ))}
              </ul>
            )}

            <footer className="flex flex-col">
              <div className="flex items-end justify-between">
                <ModerationStatusSelect
                  onChange={onModerationStatusChange}
                  disabled={moderationSaveState.type === 'saving'}
                  selected={annotation.moderation_status}
                  mode="select"
                  alignListbox="left"
                />
                <div className="flex items-center gap-1">
                  <Link
                    variant="text-light"
                    href={annotation.links.incontext}
                    target="_blank"
                    title="See in context"
                    aria-label="See in context"
                    data-testid="context-link"
                  >
                    <ExternalIcon />
                  </Link>
                  <AnnotationShareControl
                    annotation={annotation}
                    group={group}
                  />
                </div>
              </div>
              <div
                role="status"
                className={classnames(
                  ['error', 'warning'].includes(moderationSaveState.type) &&
                    'mt-2',
                )}
              >
                {moderationSaveState.type === 'error' && (
                  <Callout data-testid="update-error" status="error">
                    {moderationSaveState.message}
                  </Callout>
                )}
                {moderationSaveState.type === 'warning' && (
                  <Callout data-testid="update-warning" status="notice">
                    {moderationSaveState.message}
                  </Callout>
                )}
              </div>
            </footer>
          </CardContent>
        </Card>
      </article>
    ),
    [
      bodyCollapsed,
      bodyCollapsible,
      annoQuote,
      annotation,
      group,
      isReply,
      moderationSaveState,
      onModerationStatusChange,
      user,
      userLink,
    ],
  );
}
