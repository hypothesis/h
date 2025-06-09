import type { APIAnnotationData } from './api';

/**
 * Return the text quote that an annotation refers to.
 */
export function quote(annotation: any): string | null {
  if (annotation.target.length === 0) {
    return null;
  }
  const target = annotation.target[0];
  if (!target.selector) {
    return null;
  }
  const quoteSel = target.selector.find(
    (s: any) => s.type === 'TextQuoteSelector',
  );
  return quoteSel ? quoteSel.exact : null;
}

/**
 * Return the label of the page that an annotation comes from.
 *
 * This is usually a 1-based page number, but can also be roman numerals etc.
 */
export function pageLabel(annotation: any): string | undefined {
  const pageSel = annotation.target[0]?.selector?.find(
    (s: any) => s.type === 'PageSelector',
  );
  return pageSel?.label;
}

type DocumentMetadata = {
  uri: string;
  domain: string;
  title: string;
};

/**
 * Extract document metadata from an annotation.
 */
function documentMetadata(annotation: APIAnnotationData): DocumentMetadata {
  const uri = annotation.uri;

  let domain;
  try {
    domain = new URL(uri).hostname;
  } catch {
    // Annotation URI parsing on the backend is very liberal compared to the URL
    // constructor. There is also some historic invalid data in h (eg [1]).
    // Hence, we must handle URL parsing failures in the client.
    //
    // [1] https://github.com/hypothesis/client/issues/3666
    domain = '';
  }
  if (domain === 'localhost') {
    domain = '';
  }

  let title = domain;
  if (annotation.document && annotation.document.title) {
    title = annotation.document.title[0];
  }

  return {
    uri,
    domain,
    title,
  };
}

export type DomainAndTitle = {
  domain: string;
  titleText: string;
  titleLink: string | null;
};

/**
 * Return the domain and title of an annotation for display on an annotation
 * card.
 */
export function domainAndTitle(annotation: APIAnnotationData): DomainAndTitle {
  return {
    domain: domainTextFromAnnotation(annotation),
    titleText: titleTextFromAnnotation(annotation),
    titleLink: titleLinkFromAnnotation(annotation),
  };
}

function titleLinkFromAnnotation(annotation: APIAnnotationData): string | null {
  let titleLink: string | null = annotation.uri;

  if (
    titleLink &&
    !(titleLink.indexOf('http://') === 0 || titleLink.indexOf('https://') === 0)
  ) {
    // We only link to http(s) URLs.
    titleLink = null;
  }

  if (annotation.links && annotation.links.incontext) {
    titleLink = annotation.links.incontext;
  }

  return titleLink;
}
/**
 * Returns the domain text from an annotation.
 */
function domainTextFromAnnotation(annotation: APIAnnotationData): string {
  const document = documentMetadata(annotation);

  let domainText = '';
  if (document.uri && document.uri.indexOf('file://') === 0 && document.title) {
    const parts = document.uri.split('/');
    const filename = parts[parts.length - 1];
    if (filename) {
      domainText = filename;
    }
  } else if (document.domain && document.domain !== document.title) {
    domainText = document.domain;
  }

  return domainText;
}

/**
 * Returns the title text from an annotation and crops it to 30 chars
 * if needed.
 */
function titleTextFromAnnotation(annotation: APIAnnotationData): string {
  const document = documentMetadata(annotation);

  let titleText = document.title;
  if (titleText.length > 30) {
    titleText = titleText.slice(0, 30) + '…';
  }

  return titleText;
}

/**
 * Parses H account names of the form 'acct:<username>@<provider>'
 * into a {username, provider} object or null if the input does not
 * match the expected form.
 */
function parseAccountID(user: string | null) {
  if (!user) {
    return null;
  }
  const match = user.match(/^acct:([^@]+)@(.+)/);
  if (!match) {
    return null;
  }
  return {
    username: match[1],
    provider: match[2],
  };
}

/**
 * Returns the username part of an account ID or an empty string.
 */
export function username(user: string | null) {
  const account = parseAccountID(user);
  return account?.username;
}
