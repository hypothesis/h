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

/**
 * Selector which indicates the time range within a video or audio file that
 * an annotation refers to.
 */
export type MediaTimeSelector = {
  type: 'MediaTimeSelector';

  /** Offset from start of media in seconds. */
  start: number;
  /** Offset from start of media in seconds. */
  end: number;
};

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
 * Selector which identifies a document region using UTF-16 character offsets
 * in the document body's `textContent`.
 */
export type TextPositionSelector = {
  type: 'TextPositionSelector';
  start: number;
  end: number;
};

/**
 * Selector which identifies a document region using XPaths and character offsets.
 */
export type RangeSelector = {
  type: 'RangeSelector';
  startContainer: string;
  endContainer: string;
  startOffset: number;
  endOffset: number;
};

/**
 * Selector which identifies the Content Document within an EPUB that an
 * annotation was made in.
 */
export type EPUBContentSelector = {
  type: 'EPUBContentSelector';

  /**
   * URL of the content document. This should be an absolute HTTPS URL if
   * available, but may be relative to the root of the EPUB.
   */
  url: string;

  /**
   * EPUB Canonical Fragment Identifier for the table of contents entry that
   * corresponds to the content document.
   */
  cfi?: string;

  /** Title of the content document. */
  title?: string;
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

export type RectShape = {
  type: 'rect';
  left: number;
  top: number;
  bottom: number;
  right: number;
};

export type PointShape = {
  type: 'point';
  x: number;
  y: number;
};

export type Shape = RectShape | PointShape;

/**
 * Selector which identifies a region of the document defined by a shape.
 *
 * # Anchors
 *
 * The shape's coordinates may be relative to an _anchor_ element within the
 * document. For example a page in a PDF or an `<img>` in an HTML document. For
 * document types where a location can be fully specified by the shape
 * coordinates alone (such as images, but not PDFs or HTML documents), the
 * anchor is optional.
 *
 * # Coordinate systems
 *
 * Shape selectors should be defined using the natural coordinate system for the
 * anchor element in the document, enabling an annotation made in one viewer to
 * be resolved to the same location in a different viewer, with different view
 * settings (zoom, rotation etc.). For common document and anchor types, these
 * are as follows:
 *
 * - For PDFs, PDF user space coordinates (points), with the origin at the
 *   bottom-left corner of the page.
 * - For images, pixels with the origin at the top-left
 */
export type ShapeSelector = {
  type: 'ShapeSelector';

  shape: Shape;

  /**
   * Specifies the element of the document that the shape is relative to.
   *
   * This can be omitted in document types such as images, where the coordinates
   * on their own can specify a unique location in the document.
   *
   * Supported values:
   *
   * - "page" - The page identified by the annotation's {@link PageSelector}.
   */
  anchor?: 'page';

  /**
   * Specifies the bounding box of the visible area of the anchor element,
   * in the same coordinates used by {@link ShapeSelector.shape}.
   *
   * This enables interpreting the coordinates in the shape relative to the
   * anchor element as a whole.
   *
   * Examples of how the visible area is determined for common document and
   * anchor types:
   *
   * - For a PDF page, the box is the intersection of the media and crop box,
   *   which is usually equal to the crop box. See https://www.pdf2go.com/blog/what-are-pdf-boxes.
   * - For an SVG, these are the coordinates of the `viewBox` element
   * - For an image, `left` and `top` are zero and `right` and `bottom` are the
   *   width and height of the image in pixels.
   */
  view?: {
    left: number;
    top: number;
    right: number;
    bottom: number;
  };

  /** The text contained inside this shape. */
  text?: string;
};

/**
 * Serialized representation of a region of a document which an annotation
 * pertains to.
 */
export type Selector =
  | TextQuoteSelector
  | TextPositionSelector
  | RangeSelector
  | EPUBContentSelector
  | MediaTimeSelector
  | PageSelector
  | ShapeSelector;

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

export type UserInfo = {
  display_name: string | null;
};

export type Mention = {
  /** Current userid for the user that was mentioned */
  userid: string;
  /** Current username for the user that was mentioned */
  username: string;
  /** Current display name for the user that was mentioned */
  display_name: string | null;
  /** Link to the user profile, if applicable */
  link: string | null;
  /** The user description/bio */
  description: string | null;
  /** The date when the user joined, in ISO format */
  joined: ISODateTime | null;

  /**
   * The userid at the moment the mention was created.
   * If the user changes their username later, this can be used to match the
   * right mention tag in the annotation text.
   */
  original_userid: string;
};

export type ModerationStatus = 'PENDING' | 'APPROVED' | 'DENIED' | 'SPAM';

/**
 * Represents an annotation as returned by the h API.
 * API docs: https://h.readthedocs.io/en/latest/api-reference/#tag/annotations
 */
export type APIAnnotationData = {
  /**
   * The server-assigned ID for the annotation. This is only set once the
   * annotation has been saved to the backend.
   */
  id?: string;

  references?: string[];
  created: string;
  flagged?: boolean;
  group: string;
  updated: string;
  tags: string[];
  text: string;
  uri: string;
  user: string;
  hidden: boolean;

  document: {
    title: string;
  };

  permissions: {
    read: string[];
    update: string[];
    delete: string[];
  };

  /**
   * The document and region this annotation refers to.
   *
   * The Hypothesis API structure allows for multiple targets, but the h
   * server only supports one target per annotation.
   */
  target: Target[];

  moderation?: {
    flagCount: number;
  };

  moderation_status: ModerationStatus;

  links: {
    /**
     * A "bouncer" URL that takes the user to see the annotation in context
     */
    incontext?: string;

    /** URL to view the annotation by itself. */
    html?: string;
  };

  user_info?: UserInfo;

  /**
   * An opaque object that contains metadata about the current context,
   * provided by the embedder via the `annotationMetadata` config.
   *
   * The Hypothesis LMS app uses this field to attach information about the
   * current assignment, course etc. to annotations.
   */
  metadata?: object;

  /**
   * List of unique users that were mentioned in the annotation text.
   * This prop will be present only if `at_mentions` is enabled.
   */
  mentions?: Mention[];
};

/**
 * Response to group annotations API
 */
export type GroupAnnotationsResponse = PaginatedResponse<APIAnnotationData>;

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
