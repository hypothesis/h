import { useMemo } from 'preact/hooks';

import type { APIAnnotationData } from '../../group-forms/utils/api';
import { quote, shape } from '../helpers/annotation-metadata';
import AnnotationBody from './AnnotationBody';
import AnnotationHeader from './AnnotationHeader';
import AnnotationQuote from './AnnotationQuote';

export type AnnotationProps = {
  annotation: APIAnnotationData;
};

export default function Annotation({ annotation }: AnnotationProps) {
  const annotationQuote = quote(annotation);
  const targetShape = useMemo(() => shape(annotation), [annotation]);

  return (
    <div className="flex flex-col gap-y-4">
      <AnnotationHeader annotation={annotation} />
      {targetShape &&
        // TODO <AnnotationThumbnail />
        null}
      {annotationQuote && <AnnotationQuote quote={annotationQuote} />}
      <AnnotationBody annotation={annotation} />
    </div>
  );
}
