import { Card, CardContent } from '@hypothesis/frontend-shared';
import { useContext } from 'preact/hooks';

import {
  AnnotationGroupInfo,
  AnnotationTimestamps,
  AnnotationUser,
  MarkdownView,
  StyledText,
} from '../../annotations-ui';
import { Config } from '../config';
import type { APIAnnotationData } from '../utils/api';

function quote(annotation: any): string | null {
  if (annotation.target.length === 0) {
    return null;
  }
  const target = annotation.target[0];
  if (!target.selector) {
    return null;
  }
  const quoteSel = target.selector.find(
    (s: any) => s.type === 'TextQuoteSelector',
  );
  return quoteSel ? quoteSel.exact : null;
}

export type AnnotationCardProps = {
  annotation: APIAnnotationData;
};

export default function AnnotationCard({ annotation }: AnnotationCardProps) {
  const config = useContext(Config)!;

  return (
    <Card>
      <CardContent>
        <header className="w-full">
          <div className="flex gap-x-1 items-center justify-between">
            <AnnotationUser
              displayName={
                annotation.user_info?.display_name ?? annotation.user
              }
            />
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
      </CardContent>
    </Card>
  );
}
