import { AnnotationDocumentInfo } from '@hypothesis/annotation-ui';

import { pageLabel } from '../utils/annotation-metadata';
import type { APIAnnotationData } from '../utils/api';

export type AnnotationDocumentProps = {
  annotation: APIAnnotationData;
};

export default function AnnotationDocument({
  annotation,
}: AnnotationDocumentProps) {
  const pageNumber = pageLabel(annotation);

  return (
    <>
      <span className="flex">
        <AnnotationDocumentInfo annotation={annotation} />
        {pageNumber && (
          <span className="text-grey-6" data-testid="comma-wrapper">
            ,{' '}
          </span>
        )}
      </span>
      {pageNumber && (
        <span className="text-grey-6" data-testid="page-number">
          p. {pageNumber}
        </span>
      )}
    </>
  );
}
