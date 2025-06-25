import { Spinner } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useEffect, useRef, useState } from 'preact/hooks';

import FormContainer from '../../forms-common/components/FormContainer';
import type { Group } from '../config';
import { useGroupAnnotations } from '../hooks/use-group-annotations';
import { useUpdateModerationStatus } from '../hooks/use-update-moderation-status';
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
  const {
    loadNextPage,
    annotations,
    loading,
    removingAnnotations,
    lastAction,
    updateAnnotationStatus,
    undoLastAction,
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

  const {
    updateModerationStatus: updateModerationStatusAPI,
    updating: updatingUndo,
  } = useUpdateModerationStatus(
    lastAction?.annotation || ({} as APIAnnotationData),
  );

  const handleUndo = async () => {
    if (!lastAction) {
      return;
    }

    try {
      // First update the API with the previous status
      await updateModerationStatusAPI(lastAction.previousStatus);
      // Then update the local state
      undoLastAction();
    } catch (error) {
      // If API call fails, we could add error handling here
      console.error('Failed to undo moderation status change:', error);
    }
  };

  return (
    <section className={classnames('flex flex-col gap-y-2', classes)}>
      {lastAction && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-3 flex items-center justify-between">
          <span className="text-sm text-yellow-800">
            Changed annotation status from{' '}
            <strong>{lastAction.previousStatus.toLowerCase()}</strong> to{' '}
            <strong>{lastAction.newStatus.toLowerCase()}</strong>
          </span>
          <button
            onClick={handleUndo}
            disabled={updatingUndo}
            className={classnames(
              'text-sm underline font-medium',
              updatingUndo
                ? 'text-yellow-600 cursor-not-allowed'
                : 'text-yellow-800 hover:text-yellow-900',
            )}
          >
            {updatingUndo ? 'Undoing...' : 'Undo'}
          </button>
        </div>
      )}
      <AnnotationListContent
        filterStatus={filterStatus}
        loading={loading}
        annotations={annotations}
        removingAnnotations={removingAnnotations}
        onAnnotationStatusChange={updateAnnotationStatus}
      />
    </section>
  );
}

type AnnotationListContentProps = {
  filterStatus?: ModerationStatus;
  loading: boolean;
  annotations?: APIAnnotationData[];
  removingAnnotations: Set<string>;
  onAnnotationStatusChange: (
    annotationId: string,
    moderationStatus: ModerationStatus,
  ) => void;
};

function AnnotationListContent({
  loading,
  annotations,
  filterStatus,
  removingAnnotations,
  onAnnotationStatusChange,
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
      {annotations?.map(anno => {
        const isRemoving = anno.id && removingAnnotations.has(anno.id);
        return (
          <div
            key={anno.id}
            className={classnames(
              'transition-all duration-500 overflow-hidden',
              {
                'opacity-0 max-h-0 -mb-2': isRemoving,
              },
            )}
            style={!isRemoving ? { maxHeight: '1000px' } : undefined}
          >
            <AnnotationCard
              annotation={anno}
              onStatusChange={moderationStatus => {
                if (anno.id) {
                  onAnnotationStatusChange(anno.id, moderationStatus);
                }
              }}
            />
          </div>
        );
      })}
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
