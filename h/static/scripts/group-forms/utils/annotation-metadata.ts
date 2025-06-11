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
