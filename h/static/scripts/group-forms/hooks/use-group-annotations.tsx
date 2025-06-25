import {
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'preact/hooks';

import { Config } from '../config';
import type { APIAnnotationData, ModerationStatus } from '../utils/api';
import { fetchGroupAnnotations } from '../utils/api/fetch-group-annotations';

export type GroupAnnotationsOptions = {
  filterStatus?: ModerationStatus;
};

export type UndoAction = {
  annotationId: string;
  previousStatus: ModerationStatus;
  newStatus: ModerationStatus;
  annotation: APIAnnotationData;
};

export type GroupAnnotationsResult = {
  /** Whether there's data being currently loaded */
  loading: boolean;
  /** The last error that occurred, if any */
  error?: string;

  /**
   * The current list of annotations.
   * It will be undefined while loading the first page of data.
   */
  annotations?: APIAnnotationData[];

  /**
   * Set of annotation IDs that are currently being removed (animating out)
   */
  removingAnnotations: Set<string>;

  /**
   * The last moderation action that can be undone
   */
  lastAction?: UndoAction;

  /**
   * A callback to load the next chunk of annotations, if any.
   * Useful to progressively load more annotations, as this hook only loads the
   * first chunk when invoked.
   */
  loadNextPage: () => void;

  /**
   * A callback to locally update the moderation status of one annotation from
   * the list, without a server request.
   *
   * If the new status does not match current filter status, the annotation will
   * be removed from the list.
   */
  updateAnnotationStatus: (
    annotationId: string,
    moderationStatus: ModerationStatus,
  ) => void;

  /**
   * A callback to undo the last moderation status change
   */
  undoLastAction: () => void;
};

export function useGroupAnnotations({
  filterStatus,
}: GroupAnnotationsOptions): GroupAnnotationsResult {
  const config = useContext(Config);
  const [annotations, setAnnotations] = useState<APIAnnotationData[]>();
  const [totalAnnotations, setTotalAnnotations] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();
  const [removingAnnotations, setRemovingAnnotations] = useState<Set<string>>(
    new Set(),
  );
  const [lastAction, setLastAction] = useState<UndoAction>();
  const updateAnnotationStatus = useCallback(
    (annotationId: string, moderationStatus: ModerationStatus) => {
      // Find the annotation to track its previous status
      const currentAnnotation = annotations?.find(
        anno => anno.id === annotationId,
      );
      if (!currentAnnotation) {
        return;
      }

      // Store the action for undo
      setLastAction({
        annotationId,
        previousStatus: currentAnnotation.moderation_status,
        newStatus: moderationStatus,
        annotation: currentAnnotation,
      });

      // Always update the annotation status optimistically first
      setAnnotations(prev =>
        prev?.reduce<APIAnnotationData[]>((annos, currentAnno) => {
          annos.push(
            currentAnno.id === annotationId
              ? { ...currentAnno, moderation_status: moderationStatus }
              : currentAnno,
          );
          return annos;
        }, []),
      );

      // If the new status doesn't match the filter, start removal animation
      if (filterStatus !== undefined && filterStatus !== moderationStatus) {
        // Start the removal animation after a brief delay to show the status change
        setTimeout(() => {
          setRemovingAnnotations(prev => new Set([...prev, annotationId]));
        }, 100);

        // Remove the annotation from the list after animation completes
        setTimeout(() => {
          setAnnotations(prev =>
            prev?.filter(anno => anno.id !== annotationId),
          );
          setRemovingAnnotations(prev => {
            const updated = new Set(prev);
            updated.delete(annotationId);
            return updated;
          });
        }, 600); // 100ms delay + 500ms animation
      }
    },
    [filterStatus, annotations],
  );

  const undoLastAction = useCallback(() => {
    if (!lastAction) {
      return;
    }

    const { annotationId, previousStatus, annotation } = lastAction;

    // If the annotation was removed and we're undoing to bring it back
    if (
      filterStatus !== undefined &&
      filterStatus !== lastAction.newStatus &&
      filterStatus === previousStatus
    ) {
      // Re-add the annotation to the list
      setAnnotations(prev => {
        if (prev?.some(anno => anno.id === annotationId)) {
          // If annotation is already in the list, just update its status
          return prev.map(anno =>
            anno.id === annotationId
              ? { ...anno, moderation_status: previousStatus }
              : anno,
          );
        } else {
          // If annotation was removed, add it back with the previous status
          return prev
            ? [...prev, { ...annotation, moderation_status: previousStatus }]
            : [{ ...annotation, moderation_status: previousStatus }];
        }
      });
    } else {
      // If the annotation is still in the list, just update its status
      setAnnotations(prev =>
        prev?.map(anno =>
          anno.id === annotationId
            ? { ...anno, moderation_status: previousStatus }
            : anno,
        ),
      );
    }

    // Clear the undo action and any removing state
    setLastAction(undefined);
    setRemovingAnnotations(prev => {
      const updated = new Set(prev);
      updated.delete(annotationId);
      return updated;
    });
  }, [lastAction, filterStatus]);

  // Used to cancel currently in-flight request, whether it's the first one or
  // any subsequent page triggered by calling `loadNextPage`.
  const requestController = useRef<AbortController>();

  const loadAnnotationsForCurrentPage = useCallback(() => {
    if (!config?.api.groupAnnotations) {
      throw new Error('groupAnnotations API config missing');
    }

    // Calculate the next page that needs to be loaded, based on the amount of
    // annotations already loaded and a fixed page size
    const pageSize = 20;
    const pageIndex = annotations?.length ? annotations.length / pageSize : 0;
    const pageNumber = pageIndex + 1;

    setLoading(true);
    fetchGroupAnnotations(config.api.groupAnnotations, {
      signal: requestController.current?.signal,
      pageNumber,
      pageSize,
      moderationStatus: filterStatus,
    })
      .then(({ annotations, total }) => {
        // Append annotations from the page to current list
        setAnnotations((prev = []) => [...prev, ...annotations]);
        setTotalAnnotations(total);
      })
      .catch((e: any) => setError(e.message))
      .finally(() => setLoading(false));
  }, [annotations?.length, config?.api.groupAnnotations, filterStatus]);

  const loadNextPage = useCallback(() => {
    if (!loading && (!annotations || annotations.length < totalAnnotations)) {
      requestController.current = new AbortController();
      loadAnnotationsForCurrentPage();
    }
  }, [annotations, loadAnnotationsForCurrentPage, loading, totalAnnotations]);

  const prevFilterStatus = useRef(filterStatus);
  useEffect(() => {
    // Every time the filter status changes, discard previous list of annotations
    // and clear any pending removals and undo actions
    if (prevFilterStatus.current !== filterStatus) {
      setAnnotations(undefined);
      setRemovingAnnotations(new Set());
      setLastAction(undefined);
    }

    prevFilterStatus.current = filterStatus;
  }, [filterStatus]);

  // When annotations is not defined, trigger first load
  useEffect(() => {
    requestController.current = new AbortController();
    if (annotations === undefined) {
      loadAnnotationsForCurrentPage();
    }
    return () => requestController.current?.abort();
  }, [annotations, loadAnnotationsForCurrentPage]);

  return {
    loading,
    annotations,
    error,
    removingAnnotations,
    lastAction,
    loadNextPage,
    updateAnnotationStatus,
    undoLastAction,
  };
}
