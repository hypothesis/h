import type { APIAnnotationData, GroupAnnotationsResponse } from '.';
import { callAPI, paginationToParams } from '.';
import type { ModerationStatus } from '../../components/ModerationStatusSelect';
import type { APIConfig } from '../../config';

export type FetchGroupAnnotationsOptions = {
  signal?: AbortSignal;
  pageNumber: number;
  pageSize: number;
  moderationStatus?: ModerationStatus;
};

export type FetchGroupAnnotationsResult = {
  annotations: APIAnnotationData[];
  total: number;
};

export async function fetchGroupAnnotations(
  { url, headers, method }: APIConfig,
  {
    signal,
    pageNumber,
    pageSize,
    moderationStatus,
  }: FetchGroupAnnotationsOptions,
): Promise<FetchGroupAnnotationsResult> {
  const query: Record<string, string | number> = paginationToParams({
    pageNumber,
    pageSize,
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

  return {
    annotations: resp.data,
    total: resp.meta.page.total,
  };
}
