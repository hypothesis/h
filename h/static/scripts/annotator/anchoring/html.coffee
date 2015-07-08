raf = require('raf')

{
  FragmentAnchor
  RangeAnchor
  TextPositionAnchor
  TextQuoteAnchor
} = require('./types')


querySelector = (type, selector, options) ->
  doQuery = (resolve, reject) ->
    try
      anchor = type.fromSelector(selector, options)
      range = anchor.toRange(options)
      resolve(range)
    catch error
      reject(error)
  return new Promise(doQuery)


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

  # Assert the quote matches the stored quote, if applicable
  maybeAssertQuote = (range) ->
    if quote?.exact? and range.toString() != quote.exact
      throw new Error('quote mismatch')
    else
      return range

  # Until we successfully anchor, we fail.
  promise = Promise.reject('unable to anchor')

  if fragment?
    promise = promise.catch ->
      return querySelector(FragmentAnchor, fragment, options)
      .then(maybeAssertQuote)

  if range?
    promise = promise.catch ->
      return querySelector(RangeAnchor, range, options)
      .then(maybeAssertQuote)

  if position?
    promise = promise.catch ->
      return querySelector(TextPositionAnchor, position, options)
      .then(maybeAssertQuote)

  if quote?
    promise = promise.catch ->
      # Note: similarity of the quote is implied.
      return querySelector(TextQuoteAnchor, quote, options)

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
