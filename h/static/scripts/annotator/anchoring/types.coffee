Annotator = require('annotator')
$ = Annotator.$
xpathRange = Annotator.Range


# Helper function for throwing common errors
missingParameter = (name) ->
  throw new Error('missing required parameter "' + name + '"')


###*
# class:: RangeAnchor(range)
#
# This anchor type represents a DOM Range.
#
# :param Range range: A range describing the anchor.
###
class RangeAnchor
  constructor: (root, range) ->
    unless root? then missingParameter('root')
    unless range? then missingParameter('range')
    @root = root
    @range = xpathRange.sniff(range).normalize(@root)

  @fromRange: (root, range) ->
    return new RangeAnchor(root, range)

  # Create and anchor using the saved Range selector.
  @fromSelector: (root, selector) ->
    data = {
      start: selector.startContainer
      startOffset: selector.startOffset
      end: selector.endContainer
      endOffset: selector.endOffset
    }
    range = new xpathRange.SerializedRange(data)
    return new RangeAnchor(root, range)

  toRange: () ->
    return @range.toRange()

  toSelector: (options = {}) ->
    range = @range.serialize(@root, options.ignoreSelector)
    return {
      type: 'RangeSelector'
      startContainer: range.start
      startOffset: range.startOffset
      endContainer: range.end
      endOffset: range.endOffset
    }

exports.RangeAnchor = RangeAnchor
exports.FragmentAnchor = require('dom-anchor-fragment')
exports.TextPositionAnchor = require('dom-anchor-text-position')
exports.TextQuoteAnchor = require('dom-anchor-text-quote')
