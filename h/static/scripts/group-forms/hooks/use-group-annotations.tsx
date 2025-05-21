import {
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'preact/hooks';

import type { ModerationStatus } from '../components/ModerationStatusSelect';
import { Config } from '../config';
import type { APIAnnotationData } from '../utils/api';
import { fetchGroupAnnotations } from '../utils/api/fetch-group-annotations';

export type GroupAnnotationsOptions = {
  filterStatus?: ModerationStatus;
};

export type GroupAnnotationsResult = {
  /** Whether there's data being currently loaded */
  loading: boolean;
  /** Whether the first page of data is currently being loaded */
  loadingFirstPage: boolean;
  /** The last error that occurred, if any */
  error?: string;

  /**
   * The current list of annotations.
   * It will be empty while loading the first page of data.
   */
  annotations: APIAnnotationData[];

  /**
   * A callback to load the next up-to-20-item chunk of annotations, if any.
   * Useful to progressively load more annotations, as this hook only loads the
   * first chunk when invoked.
   */
  loadNextPage: () => void;
};

export function useGroupAnnotations({
  filterStatus,
}: GroupAnnotationsOptions): GroupAnnotationsResult {
  const config = useContext(Config);
  const [annotations, setAnnotations] = useState<APIAnnotationData[]>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();

  const pageNumberRef = useRef(1);
  const totalAnnotationsRef = useRef(0);

  /**
   * Used to cancel currently in-flight request, whether it's the first one or
   * any subsequent page triggered by calling `loadNextPage`.
   */
  const requestController = useRef<AbortController>();

  const loadAnnotationsForCurrentPage = useCallback(() => {
    if (!config?.api.groupAnnotations) {
      throw new Error('groupAnnotations API config missing');
    }

    setLoading(true);
    fetchGroupAnnotations(config.api.groupAnnotations, {
      signal: requestController.current?.signal,
      pageNumber: pageNumberRef.current,
      moderationStatus: filterStatus,
    })
      .then(({ annotations, total }) => {
        // Append annotations from the page to current list
        setAnnotations((prev = []) => [...prev, ...annotations]);
        totalAnnotationsRef.current = total;
      })
      .catch((e: any) => setError(e.message))
      .finally(() => setLoading(false));
  }, [config?.api.groupAnnotations, filterStatus]);

  const loadNextPage = useCallback(() => {
    if (
      !loading &&
      (!annotations || annotations.length < totalAnnotationsRef.current)
    ) {
      requestController.current = new AbortController();
      pageNumberRef.current++;
      loadAnnotationsForCurrentPage();
    }
  }, [annotations, loadAnnotationsForCurrentPage, loading]);

  const prevFilterStatus = useRef(filterStatus);
  useEffect(() => {
    // Every time the filter status changes, discard previous list of
    // annotations and reset the page number
    if (prevFilterStatus.current !== filterStatus) {
      setAnnotations(undefined);
      pageNumberRef.current = 1;
    }

    prevFilterStatus.current = filterStatus;

    requestController.current = new AbortController();
    loadAnnotationsForCurrentPage();

    return () => requestController.current?.abort();
  }, [filterStatus, loadAnnotationsForCurrentPage]);

  return {
    loading,
    loadingFirstPage: loading && annotations === undefined,
    annotations: annotations ?? [],
    error,
    loadNextPage,
  };
}
