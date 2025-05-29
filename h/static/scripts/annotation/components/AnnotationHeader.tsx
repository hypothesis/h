import { HighlightIcon } from '@hypothesis/frontend-shared';
import { useContext, useMemo } from 'preact/hooks';

import { Config } from '../../group-forms/config';
import type { APIAnnotationData } from '../../group-forms/utils/api';
import { username } from '../helpers/account-id';
import { hasBeenEdited, isHighlight } from '../helpers/annotation-metadata';
import AnnotationGroupInfo from './AnnotationGroupInfo';
import AnnotationTimestamps from './AnnotationTimestamps';
import AnnotationUser from './AnnotationUser';

export type AnnotationHeaderProps = {
  annotation: APIAnnotationData;
};

export default function AnnotationHeader({
  annotation,
}: AnnotationHeaderProps) {
  const config = useContext(Config)!;
  const { group } = config.context;
  const displayName = annotation.user_info?.display_name;
  const authorName =
    config.features.display_names_enabled && displayName
      ? displayName
      : username(annotation.user);

  const annotationURL = annotation.links?.html || '';

  const showEditedTimestamp = useMemo(
    () => hasBeenEdited(annotation),
    [annotation],
  );

  return (
    <header>
      <div className="flex gap-x-1 items-center flex-wrap-reverse">
        <AnnotationUser displayName={authorName} />

        <div className="flex justify-end grow">
          <AnnotationTimestamps
            annotationCreated={annotation.created}
            annotationUpdated={annotation.updated}
            annotationURL={annotationURL}
            withEditedTimestamp={showEditedTimestamp}
          />
        </div>
      </div>

      <div
        className="flex gap-x-1 items-baseline flex-wrap-reverse"
        data-testid="extended-header-info"
      >
        {group && <AnnotationGroupInfo group={group} />}
        {isHighlight(annotation) && (
          <HighlightIcon
            title="This is a highlight."
            className="w-[10px] h-[10px] text-color-text-light"
          />
        )}
      </div>
    </header>
  );
}
