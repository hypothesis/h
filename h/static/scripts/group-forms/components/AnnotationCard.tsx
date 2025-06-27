import {
  AnnotationGroupInfo,
  AnnotationShareControl,
  AnnotationTimestamps,
  AnnotationUser,
  MarkdownView,
  StyledText,
} from '@hypothesis/annotation-ui';
import {
  Card,
  CardContent,
  ExternalIcon,
  Link,
  ReplyIcon,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useCallback, useContext, useMemo, useState } from 'preact/hooks';

import { Config } from '../config';
import { useUpdateModerationStatus } from '../hooks/use-update-moderation-status';
import { quote, username } from '../utils/annotation-metadata';
import type { APIAnnotationData, ModerationStatus } from '../utils/api';
import AnnotationDocument from './AnnotationDocument';
import ModerationStatusSelect from './ModerationStatusSelect';

export type AnnotationCardProps = {
  annotation: APIAnnotationData;

  /**
   * Invoked after successfully changing the moderation status for this
   * annotation
   */
  onStatusChange: (moderationStatus: ModerationStatus) => void;
};

type SaveState =
  | { type: 'saved' }
  | { type: 'saving' }
  | { type: 'error'; error: string };

export default function AnnotationCard({
  annotation,
  onStatusChange,
}: AnnotationCardProps) {
  const config = useContext(Config)!;
  const user =
    annotation.user_info?.display_name ??
    username(annotation.user) ??
    annotation.user;
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
      } catch {
        // TODO Catching all errors generally for now, but we need to explicitly
        //      handle conflict errors
        setModerationSaveState({
          type: 'error',
          error: 'An error occurred updating the moderation status',
        });
      }
    },
    [onStatusChange, updateModerationStatus],
  );

  return (
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
              <AnnotationUser displayName={user} />
              <AnnotationTimestamps
                annotationCreated={annotation.created}
                annotationUpdated={annotation.updated}
                withEditedTimestamp={annotation.updated !== annotation.created}
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

          <StyledText>
            <blockquote className="hover:border-l-blue-quote">
              {quote(annotation)}
            </blockquote>
          </StyledText>

          <MarkdownView
            markdown={annotation.text}
            mentions={annotation.mentions}
            mentionMode="username"
            mentionsEnabled
            classes="text-color-text"
          />

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

          <footer className="flex flex-col gap-2">
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
                <AnnotationShareControl annotation={annotation} group={group} />
              </div>
            </div>
            {moderationSaveState.type === 'error' && (
              <div data-testid="update-error" className="text-red-error">
                {moderationSaveState.error}
              </div>
            )}
          </footer>
        </CardContent>
      </Card>
    </article>
  );
}
