import type {
  APIAnnotationData,
  ShapeSelector,
  TextQuoteSelector,
} from '../../group-forms/utils/api';

/**
 * Return `true` if `annotation` has a selector.
 *
 * An annotation which has a selector refers to a specific part of a document,
 * as opposed to a Page Note which refers to the whole document or a reply,
 * which refers to another annotation.
 */
function hasSelector(annotation: APIAnnotationData): boolean {
  return !!(
    annotation.target &&
    annotation.target.length > 0 &&
    annotation.target[0].selector
  );
}

/**
 * Return `true` if the given annotation is a reply, `false` otherwise.
 */
export function isReply(annotation: APIAnnotationData): boolean {
  return (annotation.references || []).length > 0;
}

/**
 * Return `true` if the given annotation is a page note.
 */
export function isPageNote(annotation: APIAnnotationData): boolean {
  return !hasSelector(annotation) && !isReply(annotation);
}

/**
 * Is this annotation a highlight?
 *
 * Highlights are generally identifiable by having no text content AND no tags,
 * but there is some nuance.
 */
export function isHighlight(annotation: APIAnnotationData): boolean {
  // Note that it is possible to end up with an empty (no `text`) annotation
  // that is not a highlight by adding at least one tag—thus, it is necessary
  // to check for the existence of tags as well as text content.

  return (
    !isPageNote(annotation) &&
    !isReply(annotation) &&
    !annotation.hidden && // A hidden annotation has some form of objectionable content
    !annotation.text &&
    !(annotation.tags && annotation.tags.length)
  );
}

/**
 * Return the text quote that an annotation refers to.
 */
export function quote(annotation: APIAnnotationData): string | null {
  if (annotation.target.length === 0) {
    return null;
  }
  const target = annotation.target[0];
  if (!target.selector) {
    return null;
  }
  const quoteSel = target.selector.find(s => s.type === 'TextQuoteSelector') as
    | TextQuoteSelector
    | undefined;
  return quoteSel ? quoteSel.exact : null;
}

/**
 * Return the shape of an annotation's target, if there is one.
 *
 * This will return `null` if the annotation is associated with a text
 * selection instead of a shape.
 */
export function shape(annotation: APIAnnotationData): ShapeSelector | null {
  const shapeSelector = annotation.target[0]?.selector?.find(
    s => s.type === 'ShapeSelector',
  ) as ShapeSelector | undefined;
  return shapeSelector ?? null;
}

/**
 * Has this annotation been edited subsequent to its creation?
 */
export function hasBeenEdited(annotation: APIAnnotationData): boolean {
  // New annotations created with the current `h` API service will have
  // equivalent (string) values for `created` and `updated` datetimes.
  // However, in the past, these values could have sub-second differences,
  // which can make them appear as having been edited when they have not
  // been. Only consider an annotation as "edited" if its creation time is
  // more than 2 seconds before its updated time.
  const UPDATED_THRESHOLD = 2000;

  // If either time string is non-extant or they are equivalent...
  if (
    !annotation.updated ||
    !annotation.created ||
    annotation.updated === annotation.created
  ) {
    return false;
  }

  // Both updated and created SHOULD be ISO-8601-formatted strings
  // with microsecond resolution; (NB: Date.prototype.getTime() returns
  // milliseconds since epoch, so we're dealing in ms after this)
  const created = new Date(annotation.created).getTime();
  const updated = new Date(annotation.updated).getTime();
  if (isNaN(created) || isNaN(updated)) {
    // If either is not a valid date...
    return false;
  }
  return updated - created > UPDATED_THRESHOLD;
}
