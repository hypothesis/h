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

/**
 * Convert pagination values into the raw record that callAPI expects as query
 *
 * @see {callAPI}
 */
export function paginationToParams({
  pageSize,
  pageNumber,
}: Pagination): Record<string, number> {
  const queryParams: Record<string, number> = {};
  if (typeof pageNumber === 'number') {
    queryParams['page[number]'] = pageNumber;
  }
  if (typeof pageSize === 'number') {
    queryParams['page[size]'] = pageSize;
  }

  return queryParams;
}
