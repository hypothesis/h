# This plugin implements the usual text anchor.
# Contains
#  * the the definitions of the corresponding selectors,
#  * the highlight class,
#  * the anchor class,
#  * the basic anchoring strategies

# Simple text highlight
class TextHighlight extends Annotator.Highlight

  # Is this element a text highlight physical anchor ?
  @isInstance: (element) -> $(element).hasClass 'annotator-hl'

  # Find the first parent outside this physical anchor
  @getIndependentParent: (element) ->
    $(element).parents(':not([class^=annotator-hl])')[0]

  # List of annotators we have already set up events for
  @_inited: []

  # Set up events for this annotator
  @_init: (annotator) ->
    return if annotator in @_inited

    getAnnotations = (event) ->
      annotations = $(event.target)
        .parents('.annotator-hl')
        .andSelf()
        .map -> return $(this).data("annotation")

    annotator.addEvent ".annotator-hl", "mouseover", (event) =>
      annotator.onAnchorMouseover getAnnotations event

    annotator.addEvent ".annotator-hl", "mouseout", (event) =>
      annotator.onAnchorMouseout getAnnotations event

    annotator.addEvent ".annotator-hl", "mousedown", (event) =>
      annotator.onAnchorMousedown getAnnotations event

    annotator.addEvent ".annotator-hl", "click", (event) =>
      annotator.onAnchorClick getAnnotations event

    @_inited.push annotator

  # Public: Wraps the DOM Nodes within the provided range with a highlight
  # element of the specified class and returns the highlight Elements.
  #
  # normedRange - A NormalizedRange to be highlighted.
  # cssClass - A CSS class to use for the highlight (default: 'annotator-hl')
  #
  # Returns an array of highlight Elements.
  _highlightRange: (normedRange, cssClass='annotator-hl') ->
    white = /^\s*$/

    hl = $("<span class='#{cssClass}'></span>")

    # Ignore text nodes that contain only whitespace characters. This prevents
    # spans being injected between elements that can only contain a restricted
    # subset of nodes such as table rows and lists. This does mean that there
    # may be the odd abandoned whitespace node in a paragraph that is skipped
    # but better than breaking table layouts.

    for node in normedRange.textNodes() when not white.test node.nodeValue
      r = $(node).wrapAll(hl).parent().show()[0]
      window.DomTextMapper.changed node, "created hilite"
      r

  # Public: highlight a list of ranges
  #
  # normedRanges - An array of NormalizedRanges to be highlighted.
  # cssClass - A CSS class to use for the highlight (default: 'annotator-hl')
  #
  # Returns an array of highlight Elements.
  _highlightRanges: (normedRanges, cssClass='annotator-hl') ->
    highlights = []
    for r in normedRanges
      $.merge highlights, this._highlightRange(r, cssClass)
    highlights

  constructor: (annotator, annotation, pageIndex, realRange) ->
    TextHighlight._init annotator
    super annotator, annotation, pageIndex
    browserRange = new Annotator.Range.BrowserRange realRange
    range = browserRange.normalize @annotator.wrapper[0]

    # Create a highlights, and link them with the annotation
    @_highlights = @_highlightRange range
    $(@_highlights).data "annotation", annotation

  # Implementing the required APIs

  # Is this a temporary hl?
  isTemporary: -> @_temporary

  # Mark/unmark this hl as active
  setTemporary: (value) ->
    @_temporary = value
    if value
      $(@_highlights).addClass('annotator-hl-temporary')
    else
      $(@_highlights).removeClass('annotator-hl-temporary')

  # Mark/unmark this hl as active
  setActive: (value) ->
    if value
      $(@_highlights).addClass('annotator-hl-active')
    else
      $(@_highlights).removeClass('annotator-hl-active')

  # Remove all traces of this hl from the document
  removeFromDocument: ->
    for hl in @_highlights
      # Is this highlight actually the part of the document?
      if hl.parentNode? and @annotator.domMapper.isPageMapped @pageIndex
        # We should restore original state
        child = hl.childNodes[0]
        $(hl).replaceWith hl.childNodes
        window.DomTextMapper.changed child.parentNode,
          "removed hilite (annotation deleted)"

  # Get the HTML elements making up the highlight
  _getDOMElements: -> @_highlights

class TextRangeAnchor extends Annotator.Anchor

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

class Annotator.Plugin.TextAnchors extends Annotator.Plugin

  # Plugin initialization
  pluginInit: ->
        
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
    $(document).bind({
      "mouseup": @checkForEndSelection
    })

    # Export this anchor type
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
    selection = Annotator.util.getGlobal().getSelection()

    ranges = []
    rangesToIgnore = []
    unless selection.isCollapsed
      ranges = for i in [0...selection.rangeCount]
        r = selection.getRangeAt(i)
        browserRange = new Annotator.Range.BrowserRange(r)
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
    $.grep ranges, (range) ->
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
      if TextHighlight.isInstance container
        container = TextHighlight.getIndependentParent container
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
    startOffset = (@annotator.domMapper.getInfoForNode rangeStart).start
    rangeEnd = range.end
    unless rangeEnd?
      throw new Error "Called getTextQuoteSelector(range) on a range with no valid end."
    endOffset = (@annotator.domMapper.getInfoForNode rangeEnd).end
    quote = @annotator.domMapper.getCorpus()[startOffset .. endOffset-1].trim()
    [prefix, suffix] = @annotator.domMapper.getContextForCharRange startOffset, endOffset

    type: "TextQuoteSelector"
    exact: quote
    prefix: prefix
    suffix: suffix

  # Create a TextPositionSelector around a range
  _getTextPositionSelector: (range) ->
    startOffset = (@annotator.domMapper.getInfoForNode range.start).start
    endOffset = (@annotator.domMapper.getInfoForNode range.end).end

    type: "TextPositionSelector"
    start: startOffset
    end: endOffset

  # Create a target around a normalizedRange
  getTargetFromRange: (range) ->
    source: @annotator.getHref()
    selector: [
      @_getRangeSelector range
      @_getTextQuoteSelector range
      @_getTextPositionSelector range
    ]

  # Stratiges used for creating these anchors from saved data

  # Look up the quote from the appropriate selector
  getQuoteForTarget: (target) ->
    selector = @annotator.findSelector target.selector, "TextQuoteSelector"
    if selector?
      @annotator.normalizeString selector.exact
    else
      null

  # Create and anchor using the saved Range selector. The quote is verified.
  createFromRangeSelector: (annotation, target) ->
    selector = @findSelector target.selector, "RangeSelector"
    unless selector? then return null

    # Try to apply the saved XPath
    try
      normalizedRange = Range.sniff(selector).normalize @wrapper[0]
    catch error
      #console.log "Could not apply XPath selector to current document, " +
      #  "because the structure has changed."
      return null
    startInfo = @domMapper.getInfoForNode normalizedRange.start
    startOffset = startInfo.start
    endInfo = @domMapper.getInfoForNode normalizedRange.end
    endOffset = endInfo.end
    content = @domMapper.getCorpus()[startOffset .. endOffset-1].trim()
    currentQuote = @normalizeString content

    # Look up the saved quote
    savedQuote = @plugins.TextAnchors.getQuoteForTarget target
    if savedQuote? and currentQuote isnt savedQuote
      #console.log "Could not apply XPath selector to current document, " +
      #  "because the quote has changed. (Saved quote is '#{savedQuote}'." +
      #  " Current quote is '#{currentQuote}'.)"
      return null

    # Create a TextRangeAnchor from this range
    new TextRangeAnchor this, annotation, target,
      startInfo.start, endInfo.end,
      (startInfo.pageIndex ? 0), (endInfo.pageIndex ? 0),
      currentQuote

  # Create an anchor using the saved TextPositionSelector. The quote is verified.
  createFromPositionSelector: (annotation, target) ->
    selector = @findSelector target.selector, "TextPositionSelector"
    unless selector? then return null
    content = @domMapper.getCorpus()[selector.start .. selector.end-1].trim()
    currentQuote = @normalizeString content
    savedQuote = @plugins.TextAnchors.getQuoteForTarget target
    if savedQuote? and currentQuote isnt savedQuote
      # We have a saved quote, let's compare it to current content
      #console.log "Could not apply position selector" +
      #  " [#{selector.start}:#{selector.end}] to current document," +
      #  " because the quote has changed. " +
      #  "(Saved quote is '#{savedQuote}'." +
      #  " Current quote is '#{currentQuote}'.)"
      return null

    # Create a TextRangeAnchor from this data
    new TextRangeAnchor this, annotation, target,
      selector.start, selector.end,
      (@domMapper.getPageIndexForPos selector.start),
      (@domMapper.getPageIndexForPos selector.end),
      currentQuote

