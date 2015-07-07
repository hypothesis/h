{
  FragmentAnchor
  RangeAnchor
  TextPositionAnchor
  TextQuoteAnchor
} = require('./types')

###*
# Anchor a set of selectors.
#
# This function converts a set of selectors into a document range using.
# It encapsulates the core anchoring algorithm, using the selectors alone or
# in combination to establish the best anchor within the document.
#
# :param Array selectors: The selectors to try.
# :return: A Promise that resolves to a Range on success.
# :rtype: Promise
####
exports.anchor = (selectors, options = {}) ->
  # Selectors
  fragment = null
  position = null
  quote = null
  range = null

  # Collect all the selectors
  for selector in selectors ? []
    switch selector.type
      when 'FragmentSelector'
        fragment = selector
      when 'TextPositionSelector'
        position = selector
        options.position = position  # TextQuoteAnchor hint
      when 'TextQuoteSelector'
        quote = selector
      when 'RangeSelector'
        range = selector

  # Until we successfully anchor, we fail.
  promise = Promise.reject('unable to anchor')

  # Assert the quote matches the stored quote, if applicable
  assertQuote = (range) ->
    if quote?.exact? and range.toString() != quote.exact
      throw new Error('quote mismatch')
    else
      return range

  if fragment?
    promise = promise.catch ->
      anchor = FragmentAnchor.fromSelector(fragment, options)
      range = anchor.toRange(options)
      assertQuote(range)
      return range

  if range?
    promise = promise.catch ->
      anchor = RangeAnchor.fromSelector(range, options)
      range = anchor.toRange(options)
      assertQuote(range)
      return range

  if position?
    promise = promise.catch ->
      anchor = TextPositionAnchor.fromSelector(position, options)
      range = anchor.toRange(options)
      assertQuote(range)
      return range

  if quote?
    promise = promise.catch ->
      anchor = TextQuoteAnchor.fromSelector(quote, options)
      return anchor.toRange(options)

  return promise


exports.describe = (range, options = {}) ->
  types = [FragmentAnchor, RangeAnchor, TextPositionAnchor, TextQuoteAnchor]

  selectors = for type in types
    try
      anchor = type.fromRange(range, options)
      selector = anchor.toSelector(options)
    catch
      continue

  return selectors
