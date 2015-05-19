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
exports.anchor = (selectors) ->
  options =
    root: document.body
    ignoreSelector: '[class^="annotator-"]'

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
      Promise.resolve(FragmentAnchor.fromSelector(fragment, options))
      .then((a) -> a.toRange(options))
      .then(assertQuote)

  if range?
    promise = promise.catch ->
      Promise.resolve(RangeAnchor.fromSelector(range, options))
      .then((a) -> a.toRange(options))
      .then(assertQuote)

  if position?
    promise = promise.catch ->
      Promise.resolve(TextPositionAnchor.fromSelector(position, options))
      .then((a) -> a.toRange(options))
      .then(assertQuote)

  if quote?
    promise = promise.catch ->
      Promise.resolve(TextQuoteAnchor.fromSelector(quote, options))
      .then((a) -> a.toRange(options))

  return promise


exports.describe = (range) ->
  options =
    root: document.body
    ignoreSelector: '[class^="annotator-"]'

  maybeDescribeWith = (type) ->
    return Promise.resolve(type)
    .then((t) -> t.fromRange(range, options))
    .then((a) -> a.toSelector(options))
    .catch(-> null)

  selectors = (maybeDescribeWith(type) for type in [
      FragmentAnchor
      RangeAnchor
      TextPositionAnchor
      TextQuoteAnchor
  ])

  return Promise.all(selectors)
  .then((selectors) -> (s for s in selectors when s?))
