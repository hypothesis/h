import {
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'preact/hooks';

import { Config } from '../config';
import type { APIAnnotationData, ModerationStatus } from '../utils/api';
import { callAPI } from '../utils/api';

/**
 * Returns a callback that can be used to update the moderation status of an
 * annotation via API call
 */
export function useUpdateModerationStatus(annotation: APIAnnotationData) {
  const config = useContext(Config);

  // Track the last in-flight request
  const abortCtrlRef = useRef<AbortController>();
  useEffect(() => {
    const abortCtrl = abortCtrlRef.current;
    return () => abortCtrl?.abort();
  }, []);

  const [updating, setUpdating] = useState(false);
  const updateModerationStatus = useCallback(
    async (moderationStatus: ModerationStatus) => {
      const annotationId = annotation.id;
      if (!config?.api.annotationModeration || !annotationId) {
        return;
      }

      const { url, ...apiConfig } = config.api.annotationModeration;

      if (abortCtrlRef.current) {
        abortCtrlRef.current.abort();
      }
      abortCtrlRef.current = new AbortController();

      setUpdating(true);
      try {
        // TODO Handle errors
        await callAPI<APIAnnotationData>(
          url.replace(':annotationId', annotationId),
          {
            ...apiConfig,
            signal: abortCtrlRef.current.signal,
            json: {
              annotation_updated: annotation.updated,
              moderation_status: moderationStatus,
            },
          },
        );
      } finally {
        setUpdating(false);
      }
    },
    [annotation.id, annotation.updated, config?.api.annotationModeration],
  );

  return {
    updating,
    updateModerationStatus,
  };
}
