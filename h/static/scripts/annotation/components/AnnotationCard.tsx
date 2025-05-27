import { Card, CardContent } from '@hypothesis/frontend-shared';
import classnames from 'classnames';

import type { APIAnnotationData } from '../../group-forms/utils/api';
import Annotation from './Annotation';

export type AnnotationCardProps = {
  annotation: APIAnnotationData;
};

/**
 * A combination of the ThreadCard and Thread components from the client repository
 */
export default function AnnotationCard({ annotation }: AnnotationCardProps) {
  return (
    <Card
      classes={classnames({
        'border-red': annotation.moderation_status === 'DENIED',
        'border-yellow': annotation.moderation_status === 'SPAM',
        'border-green': annotation.moderation_status === 'APPROVED',
      })}
    >
      <CardContent>
        <div
          className={classnames(
            // Set a max-width to ensure that annotation content does not exceed
            // the width of the container
            'grow max-w-full min-w-0',
          )}
        >
          <Annotation annotation={annotation} />
        </div>
      </CardContent>
    </Card>
  );
}
