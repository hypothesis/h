import {
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'preact/hooks';

import { GroupFormsConfig } from '../config';
import type { APIAnnotationData, ModerationStatus } from '../util/api';
import { fetchGroupAnnotations } from '../util/api/fetch-group-annotations';

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
   * Number of annotations in the `annotations` list which are not in the
   * `removedAnnotations` set.
   */
  visibleAnnotations: number;

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
  const config = useContext(GroupFormsConfig);
  const [annotations, setAnnotations] = useState<APIAnnotationData[]>();
  const [totalAnnotations, setTotalAnnotations] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();
  const [removedAnnotations, setRemovedAnnotations] = useState(
    new Set<string>(),
  );

  // We are assuming `removedAnnotations` will only include annotations that
  // have been previously loaded and therefore are part of `annotations`.
  const visibleAnnotations = annotations
    ? annotations.length - removedAnnotations.size
    : 0;

  // We can continue loading annotations if no annotations have been loaded at
  // all yet, or we have loaded less than the total number of annotations in
  // the group.
  const canLoadMoreAnnotations =
    !annotations || visibleAnnotations < totalAnnotations;

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

  // Used to cancel currently in-flight request when this is unmounted
  const abortController = useRef<AbortController | null>(null);

  const loadAnnotations = useCallback(
    (pageSize: number) => {
      if (!config?.api.groupAnnotations) {
        throw new Error('groupAnnotations API config missing');
      }

      // We only want one request to be in flight at a time. If a second one is
      // attempted, ignore it.
      // istanbul ignore next
      if (abortController.current) {
        console.warn(
          'Ignored annotations loading request, since another one is already in progress',
        );
        return;
      }
      abortController.current = new AbortController();

      // Calculate the cursor for the next page, based on the oldest annotation
      // already loaded
      const after = annotations?.[annotations.length - 1].created;

      setLoading(true);
      fetchGroupAnnotations(config.api.groupAnnotations, {
        signal: abortController.current.signal,
        moderationStatus: filterStatus,
        after,
        pageSize,
      })
        .then(({ annotations, total }) => {
          // Append annotations from the page to current list
          setAnnotations((prev = []) => [...prev, ...annotations]);
          setTotalAnnotations(total);
        })
        .catch((e: any) => setError(e.message))
        .finally(() => {
          abortController.current = null;
          setLoading(false);
        });
    },
    [annotations, config?.api.groupAnnotations, filterStatus],
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

      if (filterStatus === undefined || filterStatus === moderationStatus) {
        return;
      }

      // Mark this annotation as removed if it doesn't match the current filter.
      // The UI will hide it with a transition.
      setRemovedAnnotations(oldRemoved => {
        const newRemoved = new Set(oldRemoved);
        newRemoved.add(annotationId);
        return newRemoved;
      });

      // Since the annotation no longer matches current filter, load one more
      // annotation at the "bottom" to keep pagination consistency
      if (canLoadMoreAnnotations) {
        loadAnnotations(1);
      }
    },
    [
      annotations,
      canLoadMoreAnnotations,
      filterStatus,
      loadAnnotations,
      updateAnnotation,
    ],
  );

  const loadFullAnnotationsPage = useCallback(
    () => loadAnnotations(20),
    [loadAnnotations],
  );

  const loadNextPage = useCallback(() => {
    if (!loading && canLoadMoreAnnotations) {
      loadFullAnnotationsPage();
    }
  }, [canLoadMoreAnnotations, loadFullAnnotationsPage, loading]);

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
    if (annotations === undefined) {
      loadFullAnnotationsPage();
    }
  }, [annotations, loadFullAnnotationsPage]);

  useEffect(() => {
    return () => abortController.current?.abort();
  }, []);

  return {
    loading,
    annotations,
    removedAnnotations,
    error,
    loadNextPage,
    updateAnnotationStatus,
    updateAnnotation,
    visibleAnnotations,
  };
}
