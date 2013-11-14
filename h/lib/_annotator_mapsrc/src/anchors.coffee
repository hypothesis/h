# Abstract anchor class.
class Anchor

  constructor: (@annotator, @annotation, @target
      @startPage, @endPage,
      @quote, @diffHTML, @diffCaseOnly) ->

    unless @annotator? then throw "annotator is required!"
    unless @annotation? then throw "annotation is required!"
    unless @target? then throw "target is required!"
    unless @startPage? then "startPage is required!"
    unless @endPage? then throw "endPage is required!"
    unless @quote? then throw "quote is required!"

    @highlight = {}

  # Return highlights for the given page
  _createHighlight: (page) ->
    throw "Function not implemented"

  # Create the missing highlights for this anchor
  realize: () =>
    return if @fullyRealized # If we have everything, go home

    # Collect the pages that are already rendered
    renderedPages = [@startPage .. @endPage].filter (index) =>
      @annotator.domMapper.isPageMapped index

    # Collect the pages that are already rendered, but not yet anchored
    pagesTodo = renderedPages.filter (index) => not @highlight[index]?

    return unless pagesTodo.length # Return if nothing to do

    # Create the new highlights
    for page in pagesTodo
      @highlight[page] = @_createHighlight page

    # Check if everything is rendered now
    @fullyRealized = renderedPages.length is @endPage - @startPage + 1

    # Announce the realization
    @annotator.publish 'anchorRealized', this

  # Remove the highliths for the given set of pages
  virtualize: (pageIndex) =>
    highlight = @highlight[pageIndex]

    return unless highlight? # No highlight for this page

    highlight.removeFromDocument()

    delete @highlight[pageIndex]

    # Mark this anchor as not fully rendered
    @fullyRealized = false

    # Announce the virtualization
    @annotator.publish 'anchorVirtualized', this

  # Virtualize and remove an anchor from all involved pages
  remove: ->
    # Go over all the pages
    for index in [@startPage .. @endPage]
      @virtualize index
      anchors = @annotator.anchors[index]
      # Remove the anchor from the list
      i = anchors.indexOf this
      anchors[i..i] = []
      # Kill the list if it's empty
      delete @annotator.anchors[index] unless anchors.length

# Text range anchor
class TextRangeAnchor extends Anchor

  constructor: (annotator, annotation, target,
      @start, @end, startPage, endPage,
      quote, diffHTML, diffCaseOnly) ->

    super annotator, annotation, target,
      startPage, endPage,
      quote, diffHTML, diffCaseOnly

    unless @start? then throw "start is required!"
    unless @end? then throw "end is required!"

  # This is how we create a highlight out of this kind of anchor
  _createHighlight: (page) ->

    # First calculate the ranges
    mappings = @annotator.domMapper.getMappingsForCharRange @start, @end, [page]

    # Get the wanted range
    range = mappings.sections[page].realRange

    # Create the highligh
    new TextHighlight @annotator, @annotation, page, range

  # Create a RangeSelector around a range
  @getRangeSelector: (annotator, range) ->
    sr = range.serialize annotator.wrapper[0]

    type: "RangeSelector"
    startContainer: sr.startContainer
    startOffset: sr.startOffset
    endContainer: sr.endContainer
    endOffset: sr.endOffset

  # Create a TextQuoteSelector around a range
  @getTextQuoteSelector: (annotator, range) ->
    unless range?
      throw new Error "Called getTextQuoteSelector(range) with null range!"

    rangeStart = range.start
    unless rangeStart?
      throw new Error "Called getTextQuoteSelector(range) on a range with no valid start."
    startOffset = (annotator.domMapper.getInfoForNode rangeStart).start
    rangeEnd = range.end
    unless rangeEnd?
      throw new Error "Called getTextQuoteSelector(range) on a range with no valid end."
    endOffset = (annotator.domMapper.getInfoForNode rangeEnd).end
    quote = annotator.domMapper.getCorpus()[startOffset .. endOffset-1].trim()
    [prefix, suffix] = annotator.domMapper.getContextForCharRange startOffset, endOffset

    type: "TextQuoteSelector"
    exact: quote
    prefix: prefix
    suffix: suffix

  # Create a TextPositionSelector around a range
  @getTextPositionSelector: (annotator, range) ->
    startOffset = (annotator.domMapper.getInfoForNode range.start).start
    endOffset = (annotator.domMapper.getInfoForNode range.end).end

    type: "TextPositionSelector"
    start: startOffset
    end: endOffset

  # Create a target, around anormalizedRange
  @getTargetFromRange: (annotator, range) ->
    source: annotator.getHref()
    selector: [
      TextRangeAnchor.getRangeSelector annotator, range
      TextRangeAnchor.getTextQuoteSelector annotator, range
      TextRangeAnchor.getTextPositionSelector annotator, range
    ]
