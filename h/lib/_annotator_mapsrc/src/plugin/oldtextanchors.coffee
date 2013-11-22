# This plugin implements the usual text anchor.
# Contains
#  * the the definitions of the corresponding selectors,
#  * the highlight class,
#  * the anchor class,
#  * the basic anchoring strategies

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

class Annotator.Plugin.OldTextAnchors extends Annotator.Plugin

  # Plugin initialization
  pluginInit: ->
    # We need text highlights
    unless @annotator.plugins.TextHighlights
      throw "The TextAnchors Annotator plugin requires the TextHighlights plugin."
    # Declare our conflict with the TextAnchors plugi
    if @annotator.plugins.TextAnchors
      throw "The TextAnchors Annotator plugin conflicts with the OldTextAnchors plugin."

    @Annotator = Annotator
    @$ = Annotator.$

    # Register our anchoring strategy
    @annotator.anchoringStrategies.push
      # Simple strategy based on DOM Range
      name: "range"
      code: @createFromRangeSelector

    # Register the event handlers required for creating a selection
    $(@annotator.wrapper).bind({
      "mouseup": @checkForEndSelection
    })

    # Export this anchor type
    @annotator.TextRangeAnchor = TextRangeAnchor

    # Configure quote comparison behavior
    @verifyQuote = @options.verifyQuote ? true

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

    type: "TextQuoteSelector"
    exact: range.text().trim()

  # Create a target around a normalizedRange
  getTargetFromRange: (range) ->
    source: @annotator.getHref()
    selector: [
      @_getRangeSelector range
      @_getTextQuoteSelector range
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
  createFromRangeSelector: (annotation, target) =>
    selector = @annotator.findSelector target.selector, "RangeSelector"
    unless selector? then return null

    # Try to apply the saved XPath
    try
      normedRange = @Annotator.Range.sniff(selector).normalize @annotator.wrapper[0]
    catch error
#      console.log "Could not apply XPath selector to current document, " +
#        "because the structure has changed."
      return null

    # Get the content of this range
    currentQuote = @annotator.normalizeString normedRange.text().trim()

    if @verifyQuote
      # Look up the saved quote
      savedQuote = @getQuoteForTarget target
      if savedQuote? and currentQuote isnt savedQuote
#        console.log "Could not apply XPath selector to current document, " +
#          "because the quote has changed. (Saved quote is '#{savedQuote}'." +
#          " Current quote is '#{currentQuote}'.)"
        return null

    # Create a TextRangeAnchor from this range
    new TextRangeAnchor @annotator, annotation, target, normedRange, currentQuote

