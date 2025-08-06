import { useCallback, useContext, useRef } from 'preact/hooks';

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

  return useCallback(
    async (moderationStatus: ModerationStatus) => {
      const annotationId = annotation.id;
      if (!config?.api.annotationModeration) {
        return;
      }

      const { url, ...apiConfig } = config.api.annotationModeration;

      if (abortCtrlRef.current) {
        abortCtrlRef.current.abort();
      }
      abortCtrlRef.current = new AbortController();

      await callAPI<APIAnnotationData>(
        url.replace(':annotationId', annotationId),
        {
          ...apiConfig,
          signal: abortCtrlRef.current.signal,
          json: {
            annotation_updated: annotation.updated,
            current_moderation_status: annotation.moderation_status,
            moderation_status: moderationStatus,
          },
        },
      );
    },
    [
      annotation.id,
      annotation.moderation_status,
      annotation.updated,
      config?.api.annotationModeration,
    ],
  );
}
