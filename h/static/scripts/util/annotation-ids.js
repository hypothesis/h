/**
 * Extracts a direct-linked annotation ID from the fragment of a URL.
 *
 * @param {string} url - The URL which may contain a '#annotations:<ID>'
 *        fragment.
 * @return {string?} The annotation ID if present
 */
export function extractIDFromURL(url) {
  try {
    // Annotation IDs are url-safe-base64 identifiers
    // See https://tools.ietf.org/html/rfc4648#page-7
    const annotFragmentMatch = url.match(/#annotations:([A-Za-z0-9_-]+)$/);
    if (annotFragmentMatch) {
      return annotFragmentMatch[1];
    } else {
      return null;
    }
  } catch {
    return null;
  }
}
