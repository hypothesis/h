import {
  isModerationStatus,
  moderationStatusInfo,
  ModerationStatusSelect,
} from '@hypothesis/annotation-ui';
import {
  useStableCallback,
  Slider,
  Spinner,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'preact/hooks';

import type { Group } from '../config';
import { useGroupAnnotations } from '../hooks/use-group-annotations';
import type { APIAnnotationData, ModerationStatus } from '../util/api';
import AnnotationCard from './AnnotationCard';
import FormContainer from './FormContainer';
import GroupFormHeader from './GroupFormHeader';

/**
 * Checks if provided element's scroll is at the bottom.
 *
 * @param threshold - Return true if the difference between the element's current
 *                    and maximum scroll position is below this value.
 *                    Defaults to 20.
 */
function elementScrollIsAtBottom(el: Element, threshold = 20): boolean {
  const scrollRemaining = el.scrollHeight - el.scrollTop - el.clientHeight;
  return scrollRemaining < threshold;
}

type AnnotationListProps = {
  filterStatus?: ModerationStatus;
  classes?: string | string[];
};

function AnnotationList({ filterStatus, classes }: AnnotationListProps) {
  const {
    loadNextPage,
    annotations,
    loading,
    removedAnnotations,
    updateAnnotationStatus,
    updateAnnotation,
  } = useGroupAnnotations({ filterStatus });

  const lastScrollPosition = useRef(0);
  useEffect(() => {
    const abortController = new AbortController();

    window.addEventListener(
      'scroll',
      () => {
        const newScrollPosition = window.scrollY;
        const isScrollingDown = newScrollPosition > lastScrollPosition.current;
        lastScrollPosition.current = newScrollPosition;

        if (
          isScrollingDown &&
          document.scrollingElement &&
          elementScrollIsAtBottom(document.scrollingElement)
        ) {
          loadNextPage();
        }
      },
      { signal: abortController.signal },
    );

    return () => abortController.abort();
  }, [loadNextPage]);

  return (
    <section className={classnames('flex flex-col gap-y-2', classes)}>
      <AnnotationListContent
        filterStatus={filterStatus}
        loading={loading}
        annotations={annotations}
        removedAnnotations={removedAnnotations}
        onAnnotationStatusChange={updateAnnotationStatus}
        onAnnotationReloaded={updateAnnotation}
      />
    </section>
  );
}

type AnnotationListContentProps = {
  filterStatus?: ModerationStatus;
  loading: boolean;
  annotations?: APIAnnotationData[];
  removedAnnotations: Set<string>;
  onAnnotationStatusChange: (
    annotationId: string,
    moderationStatus: ModerationStatus,
  ) => void;
  onAnnotationReloaded: (
    annotationId: string,
    annotation: APIAnnotationData,
  ) => void;
};

function AnnotationListContent({
  loading,
  annotations,
  removedAnnotations,
  filterStatus,
  onAnnotationStatusChange,
  onAnnotationReloaded,
}: AnnotationListContentProps) {
  const onAnnotationStatusChangeStable = useStableCallback(
    onAnnotationStatusChange,
  );
  const cards = useMemo(
    () =>
      annotations?.map(anno => (
        <Slider
          key={anno.id}
          direction={removedAnnotations.has(anno.id) ? 'out' : 'in'}
          delay="0.5s"
        >
          <AnnotationCard
            annotation={anno}
            onStatusChange={moderationStatus => {
              onAnnotationStatusChangeStable(anno.id, moderationStatus);
            }}
            onAnnotationReloaded={newAnnotationData =>
              onAnnotationReloaded(anno.id, newAnnotationData)
            }
          />
        </Slider>
      )),
    [
      annotations,
      removedAnnotations,
      onAnnotationStatusChangeStable,
      onAnnotationReloaded,
    ],
  );

  if (annotations && annotations.length === 0) {
    return (
      <div
        className="border rounded p-2 text-center"
        data-testid="annotations-fallback-message"
      >
        {!filterStatus && 'There are no annotations in this group.'}
        {filterStatus && (
          <>
            There are no{' '}
            <span className="lowercase">
              {moderationStatusInfo[filterStatus].label}
            </span>{' '}
            annotations in this group.
          </>
        )}
      </div>
    );
  }

  return (
    <>
      {cards}
      {loading && (
        <div className="mx-auto mt-3">
          <Spinner size="md" />
        </div>
      )}
    </>
  );
}

export type GroupModerationProps = {
  /** The group to be moderated */
  group: Group;
};

const MODERATION_STATUS_QUERY_PARAM = 'moderation_status';

/**
 * Determines the initial moderation status, based on the optional presence of
 * the `moderation_status` query param:
 * - `PENDING` as the default value if no `moderation_status` query param is set,
 *   or it is set with an invalid value.
 * - `undefined` if the `moderation_status` query param is set to `ALL`.
 * - Any other valid moderation status set in `moderation_status` query param is
 *   returned as is.
 */
function getInitialFilterStatus(): ModerationStatus | undefined {
  const query = new URLSearchParams(window.location.search);
  if (!query.has(MODERATION_STATUS_QUERY_PARAM)) {
    return 'PENDING';
  }

  const statusFromQuery = query.get(MODERATION_STATUS_QUERY_PARAM)!;
  if (statusFromQuery === 'ALL') {
    return undefined;
  }

  // If an invalid moderation status is set, we fall back to PENDING, as if the
  // param was not set at all
  return isModerationStatus(statusFromQuery) ? statusFromQuery : 'PENDING';
}

/**
 * Sets provided moderation status in the query string.
 * If the status is `undefined`, the value `ALL` is set as a placeholder.
 */
function setFilterStatusInQuery(status?: ModerationStatus) {
  const url = new URL(window.location.href);
  url.searchParams.set(MODERATION_STATUS_QUERY_PARAM, status ?? 'ALL');
  history.replaceState(null, '', url);
}

export default function GroupModeration({ group }: GroupModerationProps) {
  const [filterStatus, setFilterStatus] = useState(getInitialFilterStatus);
  const updateFilterStatus = useCallback((status?: ModerationStatus) => {
    setFilterStatus(status);
    setFilterStatusInQuery(status);
  }, []);

  return (
    <FormContainer>
      <GroupFormHeader title="Moderate group" group={group} />
      <div className="flex justify-end">
        <ModerationStatusSelect
          selected={filterStatus}
          onChange={updateFilterStatus}
          mode="filter"
        />
      </div>
      <AnnotationList filterStatus={filterStatus} classes="mt-4" />
    </FormContainer>
  );
}
