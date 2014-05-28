# This anhor type stores information about a piece of text,
# described using the actual reference to the range in the DOM.
#
# When creating this kind of anchor, you are supposed to pass
# in a NormalizedRange object, which should cover exactly
# the wanted piece of text; no character offset correction is supported.
#
# Also, please note that these anchors can not really be virtualized,
# because they don't have any truly DOM-independent information;
# the core information stored is the reference to an object which
# lives in the DOM. Therefore, no lazy loading is possible with
# this kind of anchor. For that, use TextPositionAnchor instead.
#
# This plugin also adds a strategy to reanchor based on range selectors.
# If the TextQuote plugin is also loaded, then it will also check
# the saved quote against what is available now.
#
# If the TextPosition plugin is loaded, it will create a TextPosition
# anchor; otherwise it will record a TextRangeAnchor.
class TextRangeAnchor extends Annotator.Anchor

  @Annotator = Annotator

  constructor: (annotator, annotation, target, @range, quote) ->

    super annotator, annotation, target, 0, 0, quote

    unless @range? then throw new Error "range is required!"

    @Annotator = TextRangeAnchor.Annotator

  # This is how we create a highlight out of this kind of anchor
  _createHighlight: ->

    # Create the highligh
    new @Annotator.TextHighlight this, 0, @range


# Annotator plugin for creating, and anchoring based on text range
# selectors
class Annotator.Plugin.TextRange extends Annotator.Plugin

  pluginInit: ->

    @Annotator = Annotator

    # Register the creator for range selectors
    @annotator.selectorCreators.push
      name: "RangeSelector"
      describe: @_getRangeSelector

    # Register our anchoring strategies
    @annotator.anchoringStrategies.push
      # Simple strategy based on DOM Range
      name: "range"
      code: @createFromRangeSelector

    # Export these anchor types
    @annotator.TextRangeAnchor = TextRangeAnchor


  # Create a RangeSelector around a range
  _getRangeSelector: (selection) =>
    return [] unless selection.type is "text range"
    sr = selection.range.serialize @annotator.wrapper[0]
    [
      type: "RangeSelector"
      startContainer: sr.startContainer
      startOffset: sr.startOffset
      endContainer: sr.endContainer
      endOffset: sr.endOffset
    ]

  # Create and anchor using the saved Range selector.
  # The quote is verified.
  createFromRangeSelector: (annotation, target) =>
    selector = @annotator.findSelector target.selector, "RangeSelector"
    unless selector? then return null

    # Try to apply the saved XPath
    try
      range = @Annotator.Range.sniff selector
      normedRange = range.normalize @annotator.wrapper[0]
    catch error
      return null

    # Get the text of this range
    currentQuote = @annotator.normalizeString if @annotator.domMapper.getInfoForNode?
      # Determine the current content of the given range using DTM

      startInfo = @annotator.domMapper.getInfoForNode normedRange.start
      startOffset = startInfo.start
      endInfo = @annotator.domMapper.getInfoForNode normedRange.end
      endOffset = endInfo.end
      @annotator.domMapper.getCorpus()[startOffset .. endOffset-1].trim()
    else
      # Determine the current content of the given range directly

      normedRange.text().trim()

    # Look up the saved quote
    savedQuote = @annotator.getQuoteForTarget? target
    if savedQuote? and currentQuote isnt savedQuote
      #console.log "Could not apply XPath selector to current document, " +
      #  "because the quote has changed. (Saved quote is '#{savedQuote}'." +
      #  " Current quote is '#{currentQuote}'.)"
      return null

    if startInfo?.start? and endInfo?.end?
      # Create a TextPositionAnchor from the start and end offsets
      # of this range
      # (to be used with dom-text-mapper)
      new @Annotator.TextPositionAnchor @annotator, annotation, target,
        startInfo.start, endInfo.end,
        (startInfo.pageIndex ? 0), (endInfo.pageIndex ? 0),
        currentQuote
    else
      # Create a TextRangeAnchor from this range
      # (to be used whithout dom-text-mapper)
      new TextRangeAnchor @annotator, annotation, target,
        normedRange, currentQuote

