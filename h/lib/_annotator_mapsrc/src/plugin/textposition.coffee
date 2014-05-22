# This anchor type stores information about a piece of text,
# described using start and end character offsets
class TextPositionAnchor extends Annotator.Anchor

  @Annotator = Annotator

  constructor: (annotator, annotation, target,
      @start, @end, startPage, endPage,
      quote, diffHTML, diffCaseOnly) ->

    super annotator, annotation, target,
      startPage, endPage,
      quote, diffHTML, diffCaseOnly

    # This pair of offsets is the key information,
    # upon which this anchor is based upon.
    unless @start? then throw new Error "start is required!"
    unless @end? then throw new Error "end is required!"

    @Annotator = TextPositionAnchor.Annotator

  # This is how we create a highlight out of this kind of anchor
  _createHighlight: (page) ->

    # First we create the range from the stored stard and end offsets
    mappings = @annotator.domMapper.getMappingsForCharRange @start, @end, [page]

    # Get the wanted range out of the response of DTM
    realRange = mappings.sections[page].realRange

    # Get a BrowserRange
    browserRange = new @Annotator.Range.BrowserRange realRange

    # Get a NormalizedRange
    normedRange = browserRange.normalize @annotator.wrapper[0]

    # Create the highligh
    new @Annotator.TextHighlight this, page, normedRange


# Annotator plugin for text position-based anchoring
class Annotator.Plugin.TextPosition extends Annotator.Plugin

  pluginInit: ->

    @Annotator = Annotator

    # Do we have the basic text anchors plugin loaded?
    unless @annotator.plugins.DomTextMapper
      console.warn "The TextPosition Annotator plugin requires the DomTextMapper plugin. Skipping."
      return

    # Register the creator for text quote selectors
    @annotator.selectorCreators.push
      name: "TextPositionSelector"
      describe: @_getTextPositionSelector

    @annotator.anchoringStrategies.push
      # Position-based strategy. (The quote is verified.)
      # This can handle document structure changes,
      # but not the content changes.
      name: "position"
      code: @createFromPositionSelector

    # Export the anchor type
    @Annotator.TextPositionAnchor = TextPositionAnchor

  # Create a TextPositionSelector around a range
  _getTextPositionSelector: (selection) =>
    return [] unless selection.type is "text range"

    startOffset = @annotator.domMapper.getStartPosForNode selection.range.start
    endOffset = @annotator.domMapper.getEndPosForNode selection.range.end

    if startOffset? and endOffset?
      [
        type: "TextPositionSelector"
        start: startOffset
        end: endOffset
      ]
    else
      # It looks like we can't determine the start and end offsets.
      # That means no valid TextPosition selector can be generated from this.
      unless startOffset?
        console.log "Warning: can't generate TextPosition selector, because",
          selection.range.start,
          "does not have a valid start position."
      unless endOffset?
        console.log "Warning: can't generate TextPosition selector, because",
          selection.range.end,
          "does not have a valid end position."
      [ ]

  # Create an anchor using the saved TextPositionSelector.
  # The quote is verified.
  createFromPositionSelector: (annotation, target) =>

    # We need the TextPositionSelector
    selector = @annotator.findSelector target.selector, "TextPositionSelector"
    return unless selector?

    unless selector.start?
      console.log "Warning: 'start' field is missing from TextPositionSelector. Skipping."
      return null

    unless selector.end?
      console.log "Warning: 'end' field is missing from TextPositionSelector. Skipping."
      return null

    content = @annotator.domMapper.getCorpus()[selector.start .. selector.end-1].trim()
    currentQuote = @annotator.normalizeString content
    savedQuote = @annotator.getQuoteForTarget? target
    if savedQuote? and currentQuote isnt savedQuote
      # We have a saved quote, let's compare it to current content
      #console.log "Could not apply position selector" +
      #  " [#{selector.start}:#{selector.end}] to current document," +
      #  " because the quote has changed. " +
      #  "(Saved quote is '#{savedQuote}'." +
      #  " Current quote is '#{currentQuote}'.)"
      return null

    # Create a TextPositionAnchor from this data
    new TextPositionAnchor @annotator, annotation, target,
      selector.start, selector.end,
      (@annotator.domMapper.getPageIndexForPos selector.start),
      (@annotator.domMapper.getPageIndexForPos selector.end),
      currentQuote

