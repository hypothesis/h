Annotator = require('annotator')
$ = Annotator.$
xpathRange = Annotator.Range

DiffMatchPatch = require('diff-match-patch')
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
    iter = document.createNodeIterator(root, NodeFilter.SHOW_TEXT, filter)

    start = seek(iter, range.start)
    end = seek(iter, range.end) + start + range.end.textContent.length
    new TextPositionAnchor(start, end)

  @fromSelector: (selector) ->
    return new TextPositionAnchor(selector.start, selector.end)

  toRange: (options = {}) ->
    root = options.root or document.body
    filter = options.filter or null

    range = document.createRange()
    iter = document.createNodeIterator(root, NodeFilter.SHOW_TEXT, filter)

    {start, end} = this
    count = seek(iter, start)
    remainder = start - count

    if iter.pointerBeforeReferenceNode
      range.setStart(iter.referenceNode, remainder)
    else
      range.setStart(iter.nextNode(), remainder)
      iter.previousNode()

    length = (end - start) + remainder
    count = seek(iter, length)
    remainder = length - count

    if iter.pointerBeforeReferenceNode
      range.setEnd(iter.referenceNode, remainder)
    else
      range.setEnd(iter.nextNode(), remainder)

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
###
class TextQuoteAnchor extends Anchor
  constructor: (@quote, @prefix='', @suffix='') ->
    unless @quote? then missingParameter('quote')

  @fromRange: (range, options = {}) ->
    root = options.root or document.body
    filter = options.filter or null

    range = new xpathRange.BrowserRange(range).normalize(root)
    iter = document.createNodeIterator(root, NodeFilter.SHOW_TEXT, filter)

    start = seek(iter, range.start)
    count = seek(iter, range.end)
    end = start + count + range.end.textContent.length

    corpus = root.textContent
    prefixStart = Math.max(start - 32, 0)

    exact = corpus.substr(start, end - start)
    prefix = corpus.substr(prefixStart, start - prefixStart)
    suffix = corpus.substr(end, 32)

    return new TextQuoteAnchor(exact, prefix, suffix)

  @fromSelector: (selector) ->
    {exact, prefix, suffix} = selector
    return new TextQuoteAnchor(exact, prefix, suffix)

  toRange: (options = {}) ->
    return this.toPositionAnchor(options).toRange()

  toSelector: ->
    selector = {
      type: 'TextQuoteSelector'
      exact: @quote
    }
    if @prefix? then selector.prefix = @prefix
    if @suffix? then selector.suffix = @suffix
    return selector

  toPositionAnchor: (options = {}) ->
    root = options.root or document.body
    dmp = new DiffMatchPatch()

    foldSlices = (acc, slice) ->
      result = dmp.match_main(root.textContent, slice, acc.loc)
      if result is -1
        throw new Error('no match found')
      acc.loc = result + slice.length
      acc.start = Math.min(acc.start, result)
      acc.end = Math.max(acc.end, result + slice.length)
      return acc

    slices = @quote.match(/(.|[\r\n]){1,32}/g)
    loc = options.position?.start ? root.textContent.length / 2

    # TODO: use the suffix
    dmp.Match_Distance = root.textContent.length * 2
    if @prefix? and @quote.length < 32
      loc = Math.max(0, loc - @prefix.length)
      result = dmp.match_main(root.textContent, @prefix, loc)
      start = result + @prefix.length
      end = start
    else
      firstSlice = slices.shift()
      result = dmp.match_main(root.textContent, firstSlice, loc)
      start = result
      end = start + firstSlice.length

    if result is -1
      throw new Error('no match found')

    loc = end
    dmp.Match_Distance = 64
    {start, end} = slices.reduce(foldSlices, {start, end, loc})

    return new TextPositionAnchor(start, end)

exports.Anchor = Anchor
exports.FragmentAnchor = FragmentAnchor
exports.RangeAnchor = RangeAnchor
exports.TextPositionAnchor = TextPositionAnchor
exports.TextQuoteAnchor = TextQuoteAnchor
