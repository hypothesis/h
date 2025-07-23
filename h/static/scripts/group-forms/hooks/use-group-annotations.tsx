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
  /**
   * Filter annotations to include only those where the moderation status
   * matches `filterStatus`.
   *
   * If `undefined`, all annotations are included.
   */
  filterStatus?: ModerationStatus;
};

export type GroupAnnotationsResult = {
  /** Whether there's data being currently loaded */
  loading: boolean;
  /** The last error that occurred, if any */
  error?: string;

  /**
   * The current list of annotations.
   *
   * This will be undefined while loading the first page of data.
   */
  annotations?: APIAnnotationData[];

  /**
   * Annotations that have been marked as removed from {@link
   * GroupAnnotationsResult.annotations}.
   *
   * When an annotation's moderation status is changed and it no longer matches
   * the current filter, the annotation is marked as removed. It is marked as
   * removed rather than actually removed so the UI can perform an exit
   * transition.
   */
  removedAnnotations: Set<string>;

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
   * be marked as removed.
   */
  updateAnnotationStatus: (
    annotationId: string,
    moderationStatus: ModerationStatus,
  ) => void;

  /**
   * A callback to locally update the information of an annotation from the
   * list, without a server request.
   */
  updateAnnotation: (
    annotationId: string,
    annotation: APIAnnotationData,
  ) => void;
};

export function useGroupAnnotations({
  filterStatus,
}: GroupAnnotationsOptions): GroupAnnotationsResult {
  const config = useContext(Config);
  const [annotations, setAnnotations] = useState<APIAnnotationData[]>();
  const [totalAnnotations, setTotalAnnotations] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();
  const [removedAnnotations, setRemovedAnnotations] = useState(
    new Set<string>(),
  );

  const updateAnnotation = useCallback(
    (annotationId: string, newAnnotationData: APIAnnotationData) => {
      setAnnotations(prev =>
        prev?.reduce<APIAnnotationData[]>((annos, currentAnno) => {
          annos.push(
            currentAnno.id === annotationId ? newAnnotationData : currentAnno,
          );
          return annos;
        }, []),
      );
    },
    [],
  );

  const updateAnnotationStatus = useCallback(
    (annotationId: string, moderationStatus: ModerationStatus) => {
      const annotationToUpdate = annotations?.find(
        anno => anno.id === annotationId,
      );
      if (!annotationToUpdate) {
        return;
      }

      // Update moderation status for annotation.
      updateAnnotation(annotationId, {
        ...annotationToUpdate,
        moderation_status: moderationStatus,
      });

      // Mark this annotation as removed if it doesn't match the current filter.
      // The UI will hide it with a transition.
      if (filterStatus !== undefined && filterStatus !== moderationStatus) {
        setRemovedAnnotations(oldRemoved => {
          const newRemoved = new Set(oldRemoved);
          newRemoved.add(annotationId);
          return newRemoved;
        });
      }
    },
    [annotations, filterStatus, updateAnnotation],
  );

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
    if (prevFilterStatus.current !== filterStatus) {
      setAnnotations(undefined);
      setRemovedAnnotations(new Set());
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
    removedAnnotations,
    error,
    loadNextPage,
    updateAnnotationStatus,
    updateAnnotation,
  };
}
