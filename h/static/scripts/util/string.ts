/**
 * Convert a `camelCase` or `CapitalCase` string to `kebab-case`
 */
export function hyphenate(name: string) {
  const uppercasePattern = /([A-Z])/g;
  return name.replace(uppercasePattern, '-$1').toLowerCase();
}

/** Convert a `kebab-case` string to `camelCase` */
export function unhyphenate(name: string) {
  const idx = name.indexOf('-');
  if (idx === -1) {
    return name;
  } else {
    const ch = (name[idx + 1] || '').toUpperCase();
    return unhyphenate(name.slice(0, idx) + ch + name.slice(idx + 2));
  }
}

/**
 * Convert a string into NFKD normalization form and remove marks (accents etc.)
 *
 * This function is used to normalize strings before search to ignore
 * differences in accents etc.
 */
export function stripMarks(str: string) {
  return str.normalize('NFKD').replace(/\p{M}/gu, '');
}
