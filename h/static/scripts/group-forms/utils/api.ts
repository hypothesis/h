/**
 * Values for `type` field when creating or updating groups.
 */
export type GroupType = 'private' | 'restricted' | 'open';

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
  username: string;
};

/**
 * Response to group members API.
 *
 * https://h.readthedocs.io/en/latest/api-reference/v2/#tag/groups/paths/~1groups~1{id}~1members/get
 */
export type GroupMembersResponse = GroupMember[];

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
}

/* Make an API call and return the parsed JSON body or throw APIError. */
export async function callAPI<R = unknown>(
  url: string,
  {
    method = 'GET',
    json = null,
    headers = {},
    signal,
  }: {
    method?: string;
    json?: object | null;
    headers?: Record<PropertyKey, unknown>;
    signal?: AbortSignal;
  } = {},
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

  let response;

  try {
    response = await fetch(url, options);
  } catch (err) {
    throw new APIError('Network request failed.', {
      cause: err as Error,
    });
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
