# This plugin implements the usual text anchor.
# Contains
#  * the the definitions of the corresponding selectors,
#  * the anchor class,
#  * the basic anchoring strategies

# This anhor type stores information about a piece of text,
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
    unless @start? then throw "start is required!"
    unless @end? then throw "end is required!"

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
class TextRangeAnchor extends Annotator.Anchor

  @Annotator = Annotator

  constructor: (annotator, annotation, target, @range, quote) ->

    super annotator, annotation, target, 0, 0, quote

    unless @range? then throw "range is required!"

    @Annotator = TextRangeAnchor.Annotator

  # This is how we create a highlight out of this kind of anchor
  _createHighlight: ->

    # Create the highligh
    new @Annotator.TextHighlight this, 0, @range


class Annotator.Plugin.TextAnchors extends Annotator.Plugin

  # Check whether we can rely on DTM
  checkDTM: -> @useDTM = @annotator.domMapper?.getCorpus?

  # Plugin initialization
  pluginInit: ->
    # We need text highlights
    unless @annotator.plugins.TextHighlights
      throw "The TextAnchors Annotator plugin requires the TextHighlights plugin."

    @Annotator = Annotator
    @$ = Annotator.$
        
    # Register our anchoring strategies
    @annotator.anchoringStrategies.push
      # Simple strategy based on DOM Range
      name: "range"
      code: @createFromRangeSelector

    @annotator.anchoringStrategies.push
      # Position-based strategy. (The quote is verified.)
      # This can handle document structure changes,
      # but not the content changes.
      name: "position"
      code: @createFromPositionSelector

    # Register the event handlers required for creating a selection
    $(@annotator.wrapper).bind({
      "mouseup": @checkForEndSelection
    })

    # Export these anchor types
    @annotator.TextPositionAnchor = TextPositionAnchor
    @annotator.TextRangeAnchor = TextRangeAnchor

    null


  # Code used to create annotations around text ranges =====================

  # Gets the current selection excluding any nodes that fall outside of
  # the @wrapper. Then returns and Array of NormalizedRange instances.
  #
  # Examples
  #
  #   # A selection inside @wrapper
  #   annotation.getSelectedRanges()
  #   # => Returns [NormalizedRange]
  #
  #   # A selection outside of @wrapper
  #   annotation.getSelectedRanges()
  #   # => Returns []
  #
  # Returns Array of NormalizedRange instances.
  _getSelectedRanges: ->
    selection = @Annotator.util.getGlobal().getSelection()

    ranges = []
    rangesToIgnore = []
    unless selection.isCollapsed
      ranges = for i in [0...selection.rangeCount]
        r = selection.getRangeAt(i)
        browserRange = new @Annotator.Range.BrowserRange(r)
        normedRange = browserRange.normalize().limit @annotator.wrapper[0]

        # If the new range falls fully outside the wrapper, we
        # should add it back to the document but not return it from
        # this method
        rangesToIgnore.push(r) if normedRange is null

        normedRange

      # BrowserRange#normalize() modifies the DOM structure and deselects the
      # underlying text as a result. So here we remove the selected ranges and
      # reapply the new ones.
      selection.removeAllRanges()

    for r in rangesToIgnore
      selection.addRange(r)

    # Remove any ranges that fell outside of @wrapper.
    @$.grep ranges, (range) ->
      # Add the normed range back to the selection if it exists.
      selection.addRange(range.toRange()) if range
      range

  # This is called then the mouse is released.
  # Checks to see if a selection has been made on mouseup and if so,
  # calls Annotator's onSuccessfulSelection method.
  # If @ignoreMouseup is set, will do nothing.
  # Also resets the @mouseIsDown property.
  #
  # event - A mouseup Event object.
  #
  # Returns nothing.
  checkForEndSelection: (event) =>
    @annotator.mouseIsDown = false

    # This prevents the note image from jumping away on the mouseup
    # of a click on icon.
    return if @annotator.ignoreMouseup

    # Get the currently selected ranges.
    selectedRanges = @_getSelectedRanges()

    for range in selectedRanges
      container = range.commonAncestor
      # TODO: what is selection ends inside a different type of highlight?
      if @Annotator.TextHighlight.isInstance container
        container = @Annotator.TextHighlight.getIndependentParent container
      return if @annotator.isAnnotator(container)

    if selectedRanges.length
      event.targets = (@getTargetFromRange(r) for r in selectedRanges)
      @annotator.onSuccessfulSelection event
    else
      @annotator.onFailedSelection event

  # Create a RangeSelector around a range
  _getRangeSelector: (range) ->
    sr = range.serialize @annotator.wrapper[0]

    type: "RangeSelector"
    startContainer: sr.startContainer
    startOffset: sr.startOffset
    endContainer: sr.endContainer
    endOffset: sr.endOffset

  # Create a TextQuoteSelector around a range
  _getTextQuoteSelector: (range) ->
    unless range?
      throw new Error "Called getTextQuoteSelector(range) with null range!"

    rangeStart = range.start
    unless rangeStart?
      throw new Error "Called getTextQuoteSelector(range) on a range with no valid start."
    rangeEnd = range.end
    unless rangeEnd?
      throw new Error "Called getTextQuoteSelector(range) on a range with no valid end."

    if @useDTM
      # Calculate the quote and context using DTM

      startOffset = (@annotator.domMapper.getInfoForNode rangeStart).start
      endOffset = (@annotator.domMapper.getInfoForNode rangeEnd).end
      quote = @annotator.domMapper.getCorpus()[startOffset .. endOffset-1].trim()
      [prefix, suffix] = @annotator.domMapper.getContextForCharRange startOffset, endOffset

      type: "TextQuoteSelector"
      exact: quote
      prefix: prefix
      suffix: suffix
    else
      # Get the quote directly from the range

      type: "TextQuoteSelector"
      exact: range.text().trim()


  # Create a TextPositionSelector around a range
  _getTextPositionSelector: (range) ->
    startOffset = (@annotator.domMapper.getInfoForNode range.start).start
    endOffset = (@annotator.domMapper.getInfoForNode range.end).end

    type: "TextPositionSelector"
    start: startOffset
    end: endOffset

  # Create a target around a normalizedRange
  getTargetFromRange: (range) ->
    # Before going any further, re-evaluate the presence of DTM
    @checkDTM()

    # Create the target
    result =
      source: @annotator.getHref()
      selector: [
        @_getRangeSelector range
        @_getTextQuoteSelector range
      ]

    if @useDTM
      # If we have DTM, then we can save a position selector, too
      result.selector.push @_getTextPositionSelector range
    result

  # Look up the quote from the appropriate selector
  getQuoteForTarget: (target) ->
    selector = @annotator.findSelector target.selector, "TextQuoteSelector"
    if selector?
      @annotator.normalizeString selector.exact
    else
      null

  # Strategies used for creating anchors from saved data

  # Create and anchor using the saved Range selector.
  # The quote is verified.
  createFromRangeSelector: (annotation, target) =>
    selector = @annotator.findSelector target.selector, "RangeSelector"
    unless selector? then return null

    # Before going any further, re-evaluate the presence of DTM
    @checkDTM()

    # Try to apply the saved XPath
    try
      range = @Annotator.Range.sniff selector
      normedRange = range.normalize @annotator.wrapper[0]
    catch error
      return null

    # Get the text of this range
    currentQuote = @annotator.normalizeString if @useDTM
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
    savedQuote = @getQuoteForTarget target
    if savedQuote? and currentQuote isnt savedQuote
      #console.log "Could not apply XPath selector to current document, " +
      #  "because the quote has changed. (Saved quote is '#{savedQuote}'." +
      #  " Current quote is '#{currentQuote}'.)"
      return null

    if @useDTM
      # Create a TextPositionAnchor from the start and end offsets
      # of this range
      # (to be used with dom-text-mapper)
      new TextPositionAnchor @annotator, annotation, target,
        startInfo.start, endInfo.end,
        (startInfo.pageIndex ? 0), (endInfo.pageIndex ? 0),
        currentQuote
    else
      # Create a TextRangeAnchor from this range
      # (to be used whithout dom-text-mapper)
      new TextRangeAnchor @annotator, annotation, target,
        normedRange, currentQuote

  # Create an anchor using the saved TextPositionSelector.
  # The quote is verified.
  createFromPositionSelector: (annotation, target) =>
    # Before going any further, re-evaluate the presence of DTM
    @checkDTM()

    # This strategy depends on dom-text-mapper
    return unless @useDTM

    # We need the TextPositionSelector
    selector = @annotator.findSelector target.selector, "TextPositionSelector"
    return unless selector?

    content = @annotator.domMapper.getCorpus()[selector.start .. selector.end-1].trim()
    currentQuote = @annotator.normalizeString content
    savedQuote = @getQuoteForTarget target
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

