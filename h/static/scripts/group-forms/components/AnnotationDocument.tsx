import { AnnotationDocumentInfo } from '@hypothesis/annotation-ui';

import { domainAndTitle, pageLabel } from '../utils/annotation-metadata';
import type { APIAnnotationData } from '../utils/api';

export type AnnotationDocumentProps = {
  annotation: APIAnnotationData;
};

export default function AnnotationDocument({
  annotation,
}: AnnotationDocumentProps) {
  const documentInfo = domainAndTitle(annotation);
  const annotationURL = annotation.links?.html || '';
  const documentLink =
    annotationURL && documentInfo.titleLink ? documentInfo.titleLink : '';
  const pageNumber = pageLabel(annotation);

  return (
    <span className="flex">
      {documentInfo.titleText && (
        <AnnotationDocumentInfo
          domain={documentInfo.domain}
          link={documentLink}
          title={documentInfo.titleText}
        />
      )}
      {pageNumber && (
        <span className="text-grey-6" data-testid="page-number">
          {documentInfo.titleText && ', '}p. {pageNumber}
        </span>
      )}
    </span>
  );
}
