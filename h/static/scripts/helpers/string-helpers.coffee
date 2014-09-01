# Shared helper methods for working with strings/unicode strings
# For unicode normalization we use the unorm library
createStringHelpers = ->
  # Current unicode combining characters
  regexSymbolsWithCombiningMarks = /([\0-\u02FF\u0370-\u1DBF\u1E00-\u20CF\u2100-\uD7FF\uDC00-\uFE1F\uFE30-\uFFFF]|[\uD800-\uDBFF][\uDC00-\uDFFF]|[\uD800-\uDBFF])([\u0300-\u036F\u1DC0-\u1DFF\u20D0-\u20FF\uFE20-\uFE2F]+)/g

  unidecode: (str, normalization = 'nfkd') ->
    # normalize
    str  = unorm[normalization](str)
    # remove combining characters and return the str
    str.replace regexSymbolsWithCombiningMarks, (_, symbol, combining) -> symbol

angular.module('h.helpers.stringHelpers', [])
.service('stringHelpers', createStringHelpers)
