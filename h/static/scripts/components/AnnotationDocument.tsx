import { AnnotationDocumentInfo } from '@hypothesis/annotation-ui';

import { pageLabel } from '../util/annotation-metadata';
import type { APIAnnotationData } from '../util/api';

export type AnnotationDocumentProps = {
  annotation: APIAnnotationData;
};

/**
 * Render some metadata about an annotation's document and link to it
 * if a link is available.
 *
 * Additionally, show the page number for annotations where it is available.
 */
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
