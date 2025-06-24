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
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useContext, useMemo } from 'preact/hooks';

import { Config } from '../config';
import { quote, username } from '../utils/annotation-metadata';
import type { APIAnnotationData } from '../utils/api';
import AnnotationDocument from './AnnotationDocument';
import ModerationStatusSelect from './ModerationStatusSelect';

export type AnnotationCardProps = {
  annotation: APIAnnotationData;
};

export default function AnnotationCard({ annotation }: AnnotationCardProps) {
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
              />
            </div>
            {group && (
              <div className="flex gap-x-1 items-baseline flex-wrap-reverse">
                <AnnotationGroupInfo group={group} />
                <AnnotationDocument annotation={annotation} />
              </div>
            )}
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

          <footer className="flex items-end justify-between">
            <ModerationStatusSelect
              onChange={/* istanbul ignore next */ () => {}}
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
          </footer>
        </CardContent>
      </Card>
    </article>
  );
}
