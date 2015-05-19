# XXX: for globals needed by DomTextMatcher
require('diff-match-patch')
require('text-match-engines')
DomTextMatcher = require('dom-text-matcher')

Annotator = require('annotator')
$ = Annotator.$
xpathRange = Annotator.Range

seek = require('dom-seek')


# Helper functions for throwing common errors
missingParameter = (name) ->
  throw new Error('missing required parameter "' + name + '"')


notImplemented = ->
  throw new Error('method not implemented')


###*
# class:: Abstract base class for anchors.
###
class Anchor
  # Create an instance of the anchor from a Range.
  @fromRange: notImplemented

  # Create an instance of the anchor from a selector.
  @fromSelector: notImplemented

  # Create a Range from the anchor.
  toRange: notImplemented

  # Create a selector from the anchor.
  toSelector: notImplemented


###*
# class:: FragmentAnchor(id)
#
# This anchor type represents a fragment identifier.
#
# :param String id: The id of the fragment for the anchor.
###
class FragmentAnchor extends Anchor
  constructor: (@id) ->
    unless @id? then missingParameter('id')

  @fromRange: (range) ->
    id = $(range.commonAncestorContainer).closest('[id]').attr('id')
    return new FragmentAnchor(id)

  @fromSelector: (selector) ->
    return new FragmentAnchor(selector.value)

  toSelector: ->
    return {
      type: 'FragmentSelector'
      value: @id
    }

  toRange: ->
    el = document.getElementById(@id)
    range = document.createRange()
    range.selectNode(el)
    return range


###*
# class:: RangeAnchor(range)
#
# This anchor type represents a DOM Range.
#
# :param Range range: A range describing the anchor.
###
class RangeAnchor extends Anchor
  constructor: (@range) ->
    unless @range? then missingParameter('range')

  @fromRange: (range) ->
    return new RangeAnchor(range)

  # Create and anchor using the saved Range selector.
  @fromSelector: (selector, options = {}) ->
    root = options.root or document.body
    data = {
      start: selector.startContainer
      startOffset: selector.startOffset
      end: selector.endContainer
      endOffset: selector.endOffset
    }
    range = new xpathRange.SerializedRange(data).normalize(root).toRange()
    return new RangeAnchor(range)

  toRange: ->
    return @range

  toSelector: (options = {}) ->
    root = options.root or document.body
    ignoreSelector = options.ignoreSelector
    range = new xpathRange.BrowserRange(@range).serialize(root, ignoreSelector)
    return {
      type: 'RangeSelector'
      startContainer: range.start
      startOffset: range.startOffset
      endContainer: range.end
      endOffset: range.endOffset
    }


###*
#  class:: TextPositionAnchor(start, end)
#
# This anchor type represents a piece of text described by start and end
# character offsets.
#
# :param Number start: The start offset for the anchor text.
# :param Number end: The end offset for the anchor text.
###
class TextPositionAnchor extends Anchor
  constructor: (@start, @end) ->
    unless @start? then missingParameter('start')
    unless @end? then missingParameter('end')

  @fromRange: (range, options = {}) ->
    root = options.root or document.body
    filter = options.filter or null

    range = new xpathRange.BrowserRange(range).normalize(root)
    iter = seek.createTextIterator(root, filter)

    iter.seek(range.start).then (count) ->
      start = count
      iter.seek(range.end).then (count) ->
        end = start + count + range.end.textContent.length
        new TextPositionAnchor(start, end)

  @fromSelector: (selector) ->
    return new TextPositionAnchor(selector.start, selector.end)

  toRange: (options = {}) ->
    root = options.root or document.body
    filter = options.filter or null

    range = document.createRange()
    iter = seek.createTextIterator(root, filter)

    {start, end} = this
    iter.seek(start).then (count) ->
      remainder = start - count
      length = remainder + (end - start)
      range.setStart(iter.referenceNode, remainder)
      iter.seek(length).then (count) ->
        remainder = length - count
        range.setEnd(iter.referenceNode, remainder)
        return range

  toSelector: ->
    return {
      type: 'TextPositionSelector'
      start: @start
      end: @end
    }


###*
#  class:: TextQuoteAnchor(quote, [prefix, [suffix, [start, [end]]]])
#
# This anchor type represents a piece of text described by a quote. The quote
# may optionally include textual context and/or a position within the text.
#
# :param String quote: The anchor text to match.
# :param String prefix: A prefix that preceeds the anchor text.
# :param String suffix: A suffix that follows the anchor text.
# :param Number start: The start offset for the anchor text.
# :param Number end: The end offset for the anchor text.
###
class TextQuoteAnchor extends Anchor
  constructor: (@quote, @prefix='', @suffix='', @start, @end) ->
    unless @quote? then missingParameter('quote')

  @fromRange: (range, options = {}) ->
    root = options.root or document.body
    filter = options.filter or null

    range = new xpathRange.BrowserRange(range).normalize(root)
    iter = seek.createTextIterator(root, filter)

    iter.seek(range.start).then (count) ->
      start = count
      iter.seek(range.end).then (count) ->
        end = start + count + range.end.textContent.length
        prefixStart = Math.max(start - 32, 0)
        corpus = root.textContent
        exact = corpus.substr(start, end - start)
        prefix = corpus.substr(prefixStart, start - prefixStart)
        suffix = corpus.substr(end, 32)
        return new TextQuoteAnchor(exact, prefix, suffix, start, end)

  @fromSelector: (selector, options = {}) ->
    {start, end} = options.position ? {}
    {exact, prefix, suffix} = selector
    return new TextQuoteAnchor(exact, prefix, suffix, start, end)

  toRange: (options = {}) ->
    root = options.root or document.body
    corpus = root.textContent
    matcher = new DomTextMatcher(-> corpus)

    options.matchDistance ?= corpus.length * 2
    options.contextMatchDistance ?= corpus.length * 2
    options.contextMatchThreshold ?= 0.5
    options.patternMatchThreshold ?= 0.5
    options.flexContext ?= true
    options.withFuzzyComparison ?= true

    if @prefix.length and @suffix.length
      result = matcher.searchFuzzyWithContext(
        @prefix, @suffix, @quote, @start, @end, true, options)

    if not result?.matches.length and @quote.length >= 32
      # For short quotes, this is bound to return false positives.
      # See https://github.com/hypothesis/h/issues/853 for details.
      result = matcher.searchFuzzy(@quote, @start, true, options)

    if result?.matches.length
      match = result.matches[0]
      positionAnchor = new TextPositionAnchor(match.start, match.end)
      return positionAnchor.toRange()

    throw new Error('no match found')

  toSelector: ->
    selector = {
      type: 'TextQuoteSelector'
      exact: @quote
    }
    if @prefix? then selector.prefix = @prefix
    if @suffix? then selector.suffix = @suffix
    return selector

exports.Anchor = Anchor
exports.FragmentAnchor = FragmentAnchor
exports.RangeAnchor = RangeAnchor
exports.TextPositionAnchor = TextPositionAnchor
exports.TextQuoteAnchor = TextQuoteAnchor
