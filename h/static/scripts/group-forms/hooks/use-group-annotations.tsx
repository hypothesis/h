import { useContext, useEffect, useState } from 'preact/hooks';

import type { ModerationStatus } from '../components/ModerationStatusSelect';
import { Config } from '../config';
import type { APIAnnotationData } from '../utils/api';
import { fetchGroupAnnotations } from '../utils/api/fetch-group-annotations';

export type GroupAnnotationsOptions = {
  filterStatus?: ModerationStatus;
};

export type GroupAnnotationsResult = {
  loading: boolean;
  error?: string;
  annotations: APIAnnotationData[];
};

export function useGroupAnnotations({
  filterStatus,
}: GroupAnnotationsOptions): GroupAnnotationsResult {
  const config = useContext(Config);
  const [annotations, setAnnotations] = useState<APIAnnotationData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();

  useEffect(() => {
    if (!config?.api.groupAnnotations) {
      throw new Error('groupAnnotations API config missing');
    }
    const abort = new AbortController();

    setLoading(true);
    fetchGroupAnnotations(config.api.groupAnnotations, {
      signal: abort.signal,
      moderationStatus: filterStatus,
    })
      .then(setAnnotations)
      .catch((e: any) => setError(e.message))
      .finally(() => setLoading(false));

    return () => abort.abort();
  }, [config?.api.groupAnnotations, filterStatus]);

  return { annotations, loading, error };
}
