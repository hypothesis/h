import type { Mention } from '@hypothesis/annotation-ui';
import type { Annotation } from '@hypothesis/annotation-ui/lib/helpers/annotation-metadata';

/**
 * Values for `type` field when creating or updating groups.
 */
export type GroupType = 'private' | 'restricted' | 'open';

/** Member role within a group. */
export type Role = 'owner' | 'admin' | 'moderator' | 'member';

/** A date and time in ISO format (eg. "2024-12-09T07:17:52+00:00") */
export type ISODateTime = string;

/**
 * Request to create or update a group.
 *
 * See https://h.readthedocs.io/en/latest/api-reference/v2/#tag/groups/paths/~1groups/post
 */
export type CreateUpdateGroupAPIRequest = {
  id?: string;
  name: string;
  description?: string;
  type?: GroupType;
  pre_moderated?: boolean;
};

/**
 * A successful response from either h's create-new-group API or its update-group API:
 *
 * https://h.readthedocs.io/en/latest/api-reference/v2/#tag/groups/paths/~1groups/post
 * https://h.readthedocs.io/en/latest/api-reference/v2/#tag/groups/paths/~1groups~1{id}/patch
 */
export type CreateUpdateGroupAPIResponse = {
  links: {
    html: string;
  };
};

export type GroupMember = {
  userid: string;
  display_name?: string;
  username: string;
  actions: string[];
  roles: Role[];

  /** Timestamp when user joined group. `null` if before Dec 2024. */
  created: ISODateTime | null;

  /** Timestamp when membership was last updated. `null` if before Dec 2024. */
  updated: ISODateTime | null;
};

export type PaginatedResponse<Item> = {
  meta: {
    page: {
      /** Total number of items in the collection. */
      total: number;
    };
  };
  data: Item[];
};

/**
 * Response to group members API.
 *
 * https://h.readthedocs.io/en/latest/api-reference/v2/#tag/groups/paths/~1groups~1{id}~1members/get
 */
export type GroupMembersResponse = PaginatedResponse<GroupMember>;

export type UserInfo = {
  display_name: string | null;
};

export type ModerationStatus = 'PENDING' | 'APPROVED' | 'DENIED' | 'SPAM';

/**
 * Selector which identifies a document region using the selected text plus
 * the surrounding context.
 */
export type TextQuoteSelector = {
  type: 'TextQuoteSelector';
  exact: string;
  prefix?: string;
  suffix?: string;
};

/**
 * Selector which identifies the page of a document that an annotation was made
 * on.
 *
 * This selector is only applicable for document types where the association of
 * content and page numbers can be done in a way that is independent of the
 * viewer and display settings. This includes inherently paginated documents
 * such as PDFs, but also content such as EPUBs when they include information
 * about the location of page breaks in printed versions of a book. It does
 * not include ordinary web pages or EPUBs without page break information
 * however.
 */
export type PageSelector = {
  type: 'PageSelector';

  /** The zero-based index of the page in the document's page sequence. */
  index: number;

  /**
   * Either the page number that is displayed on the page, or the 1-based
   * number of the page in the document's page sequence, if the pages do not
   * have numbers on them.
   */
  label?: string;
};

/**
 * Serialized representation of a region of a document which an annotation
 * pertains to.
 */
export type Selector = TextQuoteSelector | PageSelector;

/**
 * An entry in the `target` field of an annotation which identifies the document
 * and region of the document that it refers to.
 */
export type Target = {
  /** URI of the document */
  source: string;
  /** Region of the document */
  selector?: Selector[];
  /** Text description of the selection, for when the selection itself is not text. */
  description?: string;
};

/**
 * Represents an annotation as returned by the h API.
 * API docs: https://h.readthedocs.io/en/latest/api-reference/#tag/annotations
 */
export type APIAnnotationData = Annotation & {
  id: string;
  text: string;

  references?: string[];
  mentions: Mention[];
  tags: string[];

  user: string;
  user_info?: UserInfo;

  created: string;
  updated: string;

  moderation_status: ModerationStatus;

  /**
   * The document and region this annotation refers to.
   *
   * The Hypothesis API structure allows for multiple targets, but the h
   * server only supports one target per annotation.
   */
  target: Target[];
};

/**
 * Response to group annotations API
 */
export type GroupAnnotationsResponse = PaginatedResponse<APIAnnotationData>;

/**
 * Request to update the authenticated user's preferences.
 */
export type UpdateUserPrefsAPIRequest = {
  preferences: {
    show_orcid_id_on_profile: boolean;
  };
};

/**
 * A successful response from h's update-user-preferences API.
 */
export type UpdateUserPrefsAPIResponse = {
  preferences: {
    show_orcid_id_on_profile?: boolean;
  };
};

/** An error response from the h API:
 * https://h.readthedocs.io/en/latest/api-reference/v2/#section/Hypothesis-API/Errors
 */
export type APIErrorResponse = {
  reason: string;
};

export class APIError extends Error {
  /* The fetch or JSON-parsing error that was the cause of this APIError, if any. */
  cause: Error | null;
  /* The response that was received, if any. */
  response: Response | null;
  /* The parsed JSON body of the response, if there was a valid JSON response. */
  json: object | Array<unknown> | null;

  constructor(
    message: string,
    {
      cause = null,
      response = null,
      json = null,
    }: {
      cause?: Error | null;
      response?: Response | null;
      json?: object | null;
    },
  ) {
    super(message);
    this.cause = cause;
    this.response = response;
    this.json = json;
  }

  /**
   * Property that is true if the API call failed because the operation was
   * aborted.
   */
  get aborted() {
    return this.cause?.name === 'AbortError';
  }
}

export type APIOptions = {
  method?: string;
  json?: object | null;
  query?: Record<string, string | number>;
  headers?: Record<PropertyKey, unknown>;
  signal?: AbortSignal;
};

/** Make an API call and return the parsed JSON body or throw APIError. */
export async function callAPI<R = unknown>(
  url: string,
  {
    headers = {},
    json = null,
    query = {},
    method = 'GET',
    signal,
  }: APIOptions = {},
): Promise<R> {
  const options: RequestInit = {
    method,
    headers: {
      ...headers,
      'Content-Type': 'application/json; charset=UTF-8',
    },
    signal,
  };

  if (json) {
    options.body = JSON.stringify(json);
  }

  const requestURL = new URL(url);
  for (const [param, value] of Object.entries(query)) {
    requestURL.searchParams.set(param, value.toString());
  }

  let response;
  try {
    // Converting `requestURL` to a string is not necessary, but it makes
    // writing tests easier.
    response = await fetch(requestURL.toString(), options);
  } catch (err) {
    throw new APIError('Network request failed.', {
      cause: err as Error,
    });
  }

  if (response.status === 204) {
    return {} as R;
  }

  let responseJSON;
  let responseJSONError;

  try {
    responseJSON = await response.json();
  } catch (jsonError) {
    responseJSONError = jsonError;
  }

  if (!response.ok) {
    responseJSON = responseJSON as APIErrorResponse;

    let message;

    if (responseJSON && responseJSON.reason) {
      message = responseJSON.reason;
    } else {
      message = 'API request failed.';
    }

    throw new APIError(message, { response, json: responseJSON });
  }

  if (responseJSONError !== undefined) {
    throw new APIError('Invalid API response.', {
      cause: responseJSONError,
      response,
    });
  }

  return responseJSON;
}

export type Pagination = {
  /** 1-based number of first page to return in paginated APIs. */
  pageNumber?: number;
  /** Maximum number of items to return in response for a paginated API. */
  pageSize?: number;
};

export type CursorPagination = {
  /** Return paginated items after this cursor */
  after?: string;
  /** Maximum number of items to return in response for a paginated API. */
  pageSize?: number;
};

/**
 * Convert pagination values into the raw record that callAPI expects as query
 *
 * @see {callAPI}
 */
export function paginationToParams({
  pageSize,
  ...rest
}: Pagination | CursorPagination): Record<string, string | number> {
  const queryParams: Record<string, string | number> = {};
  if ('after' in rest && rest.after) {
    queryParams['page[after]'] = rest.after;
  }
  if ('pageNumber' in rest && typeof rest.pageNumber === 'number') {
    queryParams['page[number]'] = rest.pageNumber;
  }
  if (typeof pageSize === 'number') {
    queryParams['page[size]'] = pageSize;
  }

  return queryParams;
}
