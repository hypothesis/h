import {
  Link,
  decayingInterval,
  formatRelativeDate,
  formatDateTime,
} from '@hypothesis/frontend-shared';
import { useEffect, useMemo, useState } from 'preact/hooks';

export type AnnotationTimestampProps = {
  annotationCreated: string;
  annotationUpdated: string;
  annotationURL?: string;
  /** Display a relative last-updated timestamp */
  withEditedTimestamp?: boolean;
};

/**
 * Render textual timestamp information for an annotation. This includes
 * a relative date string (e.g. "5 hours ago") for the annotation's creation,
 * and, if `withEditedTimestamp` is `true`, a relative date string for when it
 * was last edited. If the `annotation` has an HTML link, the created-date
 * timestamp will be linked to that URL (the single-annotation view
 * for this annotation).
 */
export default function AnnotationTimestamps({
  annotationCreated,
  annotationUpdated,
  annotationURL,
  withEditedTimestamp,
}: AnnotationTimestampProps) {
  // "Current" time, used when calculating the relative age of `timestamp`.
  const [now, setNow] = useState(() => new Date());
  const createdDate = useMemo(
    () => new Date(annotationCreated),
    [annotationCreated],
  );
  const updatedDate = useMemo(
    () => withEditedTimestamp && new Date(annotationUpdated),
    [annotationUpdated, withEditedTimestamp],
  );

  const created = useMemo(() => {
    return {
      absolute: formatDateTime(createdDate, { includeWeekday: true }),
      relative: formatRelativeDate(createdDate, now),
    };
  }, [createdDate, now]);

  const updated = useMemo(() => {
    if (!updatedDate) {
      return {};
    }
    return {
      absolute: formatDateTime(updatedDate, { includeWeekday: true }),
      relative: formatRelativeDate(updatedDate, now),
    };
  }, [updatedDate, now]);

  // Refresh relative timestamp, at a frequency appropriate for the age.
  useEffect(() => {
    // Determine which of the two Dates to use for the `decayingInterval`
    // It should be the latest relevant date, as the interval will be
    // shorter the closer the date is to "now"
    const laterDate = updatedDate ? annotationUpdated : annotationCreated;
    const cancelRefresh = decayingInterval(laterDate, () => setNow(new Date()));
    return cancelRefresh;
  }, [annotationCreated, annotationUpdated, createdDate, updatedDate, now]);

  // Do not show the relative timestamp for the edited date if it is the same
  // as the relative timestamp for the created date
  const editedString =
    updated && updated.relative !== created.relative
      ? `edited ${updated.relative}`
      : 'edited';

  return (
    <div>
      {withEditedTimestamp && (
        <span
          className="text-color-text-light text-xs italic"
          data-testid="timestamp-edited"
          title={updated.absolute}
        >
          ({editedString}){' '}
        </span>
      )}
      {annotationURL ? (
        <Link
          // The light-text hover color is not a standard color for a Link, so
          // LinkBase is used here
          classes="text-color-text-light hover:text-color-text-light"
          target="_blank"
          title={created.absolute}
          href={annotationURL}
          underline="hover"
          variant="custom"
        >
          {created.relative}
        </Link>
      ) : (
        <span
          className="color-text-color-light"
          data-testid="timestamp-created"
          title={created.absolute}
        >
          {created.relative}
        </span>
      )}
    </div>
  );
}
