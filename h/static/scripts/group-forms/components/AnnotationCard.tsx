import {
  AnnotationGroupInfo,
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
  ShareIcon,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useContext } from 'preact/hooks';

import { Config } from '../config';
import { quote, username } from '../utils/annotation-metadata';
import type { APIAnnotationData } from '../utils/api';
import AnnotationDocument from './AnnotationDocument';

export type AnnotationCardProps = {
  annotation: APIAnnotationData;
};

export default function AnnotationCard({ annotation }: AnnotationCardProps) {
  const config = useContext(Config)!;
  const user =
    annotation.user_info?.display_name ??
    username(annotation.user) ??
    annotation.user;

  return (
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
          {config.context.group && (
            <div className="flex gap-x-1 items-baseline flex-wrap-reverse">
              <AnnotationGroupInfo
                group={{
                  type: config.context.group.type,
                  name: config.context.group.name,
                  links: {
                    html: config.context.group.link,
                  },
                }}
              />
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
          <ul className="flex flex-wrap gap-1 text-sm">
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

        <footer className="flex items-center justify-between">
          <div />
          <div className="flex items-center gap-3">
            <Link
              variant="text-light"
              href={annotation.links.incontext}
              title="See in context"
              aria-label="See in context"
            >
              <ExternalIcon />
            </Link>
            <ShareIcon />
          </div>
        </footer>
      </CardContent>
    </Card>
  );
}
