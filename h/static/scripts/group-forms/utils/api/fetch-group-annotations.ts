import type { APIAnnotationData, GroupAnnotationsResponse } from '.';
import { callAPI, paginationToParams } from '.';
import type { ModerationStatus } from '../../components/ModerationStatusSelect';
import type { APIConfig } from '../../config';

export type FetchGroupAnnotationsOptions = {
  signal: AbortSignal;
  pageNumber?: number;
  moderationStatus?: ModerationStatus;
};

export async function fetchGroupAnnotations(
  { url, headers, method }: APIConfig,
  { signal, pageNumber = 1, moderationStatus }: FetchGroupAnnotationsOptions,
): Promise<APIAnnotationData[]> {
  const query: Record<string, string | number> = paginationToParams({
    pageNumber,
    pageSize: 20,
  });
  if (moderationStatus) {
    query.moderation_status = moderationStatus;
  }

  const resp = await callAPI<GroupAnnotationsResponse>(url, {
    headers,
    method,
    query,
    signal,
  });

  return resp.data;
}
