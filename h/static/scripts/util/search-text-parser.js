/**
 * Function which determines if it is possible to lozengify a given phrase.
 *
 * @param {string} phrase A potential query term.
 *
 * @returns {boolean} True if the input phrase can be lozengified and false otherwise.
 *
 * @example
 * // returns True
 * canLozengify('foo')
 * @example
 * // returns False
 * canLozengify('foo)
 */
function canLozengify(phrase) {
  phrase = phrase.trim();
  // if there is no word
  if (!phrase) {
    return false;
  }
  // if a phrase starts with a double quote, it has to have a closing double quote
  if (
    phrase.indexOf('"') === 0 &&
    (phrase.indexOf('"', 1) > phrase.length - 1 || phrase.indexOf('"', 1) < 0)
  ) {
    return false;
  }
  // if a phrase starts with a single quote, it has to have a closing double quote
  if (
    phrase.indexOf("'") === 0 &&
    (phrase.indexOf("'", 1) > phrase.length - 1 || phrase.indexOf("'", 1) < 0)
  ) {
    return false;
  }
  // if phrase ends with a double quote it has to start with one
  if (
    phrase.indexOf('"', 1) === phrase.length - 1 &&
    phrase.indexOf('"') !== 0
  ) {
    return false;
  }
  // if phrase ends with a single quote it has to start with one
  if (
    phrase.indexOf("'", 1) === phrase.length - 1 &&
    phrase.indexOf("'") !== 0
  ) {
    return false;
  }
  return true;
}

/**
 * Function which determines if a phrase can be lozengified as is or
 * if it needs to be divided into a facet name and value first.
 *
 * @param {string} phrase A potential query term.
 *
 * @returns {boolean} True if the input phrase is ready to be
 * lozengified and false otherwise.
 *
 * @example
 * // returns True
 * shouldLozengify('foo:bar')
 * @example
 * // returns False
 * shouldLozengify('foo:"bar')
 */
export function shouldLozengify(phrase) {
  // if the phrase has a facet and value
  if (phrase.indexOf(':') >= 0) {
    const queryTerm = getLozengeFacetNameAndValue(phrase);

    if (!canLozengify(queryTerm.facetName)) {
      return false;
    }
    if (
      queryTerm.facetValue.length > 0 &&
      !canLozengify(queryTerm.facetValue)
    ) {
      return false;
    }
  } else if (!canLozengify(phrase)) {
    return false;
  }
  return true;
}

/**
 * Return an array of lozenge values from the given string.
 *
 * @param {string} queryString A string of query terms.
 *
 * @returns {Object} An object with two properties: lozengeValues is an array
 *   of values to be turned into lozenges, and incompleteInputValue is any
 *   remaining un-lozengifiable text from the end of the input string
 *
 * @example
 * // returns {
 *   'lozengeValues': ['foo', 'key:"foo bar"', 'gar'],
 *   'incompleteInputValue': '"unclosed',
 * }
 * getLozengeValues('foo key:"foo bar" gar "unclosed')
 */
export function getLozengeValues(queryString) {
  let inputTerms = '';
  let quoted;
  const queryTerms = [];
  queryString.split(' ').forEach(term => {
    if (quoted) {
      inputTerms = inputTerms + ' ' + term;
      if (shouldLozengify(inputTerms)) {
        queryTerms.push(inputTerms);
        inputTerms = '';
        quoted = false;
      }
    } else if (shouldLozengify(term)) {
      queryTerms.push(term);
    } else {
      inputTerms = term;
      quoted = true;
    }
  });
  return {
    lozengeValues: queryTerms,
    incompleteInputValue: inputTerms,
  };
}

/**
 * Return true if the input query term string has a known named
 * query term.
 *
 * @param {string} queryTerm The query term string.
 *
 * @returns {boolean} True if the query term string has a known named
 * query term and False otherwise.
 *
 * @example
 * // returns false
 * hasKnownNamedQueryTerm('foo:bar')
 * @example
 * // returns true
 * hasKnownNamedQueryTerm('user:foo')
 */
export function hasKnownNamedQueryTerm(queryTerm) {
  const knownNamedQueryTerms = ['user', 'uri', 'url', 'group', 'tag'];

  const facetName = getLozengeFacetNameAndValue(queryTerm).facetName;

  return knownNamedQueryTerms.indexOf(facetName) >= 0;
}

/**
 * Return an object with the facet name and value for a given query term.
 *
 * @param {string} queryTerm The query term string.
 *
 * @returns {Object} An object with two properties:
 * facetName and facetValue.
 *
 * @example
 * // returns {
 *   facetName: foo,
 *   facetValue: bar,
 * }
 * getLozengeFacetNameAndValue('foo:bar')
 * @example
 * // returns {
 *   facetName: '',
 *   facetValue: gar,
 * }
 * getLozengeFacetNameAndValue('gar')
 */
export function getLozengeFacetNameAndValue(queryTerm) {
  let i;
  const lozengeFacetNameAndValue = {
    facetName: '',
    facetValue: '',
  };

  if (queryTerm.indexOf(':') >= 0) {
    i = queryTerm.indexOf(':');

    lozengeFacetNameAndValue.facetName = queryTerm.slice(0, i).trim();
    lozengeFacetNameAndValue.facetValue = queryTerm
      .slice(i + 1, queryTerm.length)
      .trim();

    return lozengeFacetNameAndValue;
  }

  lozengeFacetNameAndValue.facetValue = queryTerm;

  return lozengeFacetNameAndValue;
}
