/**
 * A successful response from h's create-new-group API:
 * https://h.readthedocs.io/en/latest/api-reference/v2/#tag/groups/paths/~1groups/post
 */
export type CreateGroupAPIResponse = {
  links: {
    html: string;
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
  json: object | Array<any> | null;

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
export async function callAPI(
  url: string,
  method: string = 'GET',
  json: object | undefined,
): Promise<object> {
  const options: RequestInit = {
    method: method,
    headers: { 'Content-Type': 'application/json; charset=UTF-8' },
  };

  if (json !== undefined) {
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
