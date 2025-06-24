import { Spinner } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useEffect, useRef, useState } from 'preact/hooks';

import FormContainer from '../../forms-common/components/FormContainer';
import type { Group } from '../config';
import { useGroupAnnotations } from '../hooks/use-group-annotations';
import type { APIAnnotationData, ModerationStatus } from '../utils/api';
import { moderationStatusToLabel } from '../utils/moderation-status';
import AnnotationCard from './AnnotationCard';
import GroupFormHeader from './GroupFormHeader';
import ModerationStatusSelect from './ModerationStatusSelect';

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
  const { loadNextPage, annotations, loading } = useGroupAnnotations({
    filterStatus,
  });

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
      />
    </section>
  );
}

type AnnotationListContentProps = {
  filterStatus?: ModerationStatus;
  loading: boolean;
  annotations?: APIAnnotationData[];
};

function AnnotationListContent({
  loading,
  annotations,
  filterStatus,
}: AnnotationListContentProps) {
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
              {moderationStatusToLabel[filterStatus]}
            </span>{' '}
            annotations in this group.
          </>
        )}
      </div>
    );
  }

  return (
    <>
      {annotations?.map(anno => (
        <AnnotationCard key={anno.id} annotation={anno} />
      ))}
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

export default function GroupModeration({ group }: GroupModerationProps) {
  const [filterStatus, setFilterStatus] = useState<
    ModerationStatus | undefined
  >('PENDING');
  return (
    <FormContainer>
      <GroupFormHeader title="Moderate group" group={group} />
      <div className="flex justify-end">
        <ModerationStatusSelect
          selected={filterStatus}
          onChange={setFilterStatus}
          mode="filter"
        />
      </div>
      <AnnotationList filterStatus={filterStatus} classes="mt-4" />
    </FormContainer>
  );
}
