# This plugin defines the TextQuote selector
class Annotator.Plugin.TextQuote extends Annotator.Plugin

  @Annotator = Annotator
  @$ = Annotator.$

  # Plugin initialization
  pluginInit: ->

    @anchoring = @annotator.anchoring

    # Register the creator for text quote selectors
    @anchoring.selectorCreators.push
      name: "TextQuoteSelector"
      describe: @_getTextQuoteSelector

    # Register function to get quote from this selector
    @anchoring.getQuoteForTarget = (target) =>
      selector = @anchoring.findSelector target.selector, "TextQuoteSelector"
      if selector?
        @anchoring.normalizeString selector.exact
      else
        null

  # Create a TextQuoteSelector around a range
  _getTextQuoteSelector: (selection) =>
    return [] unless selection.type is "text range"

    document = @anchoring.document

    unless selection.range?
      throw new Error "Called getTextQuoteSelector() with null range!"

    rangeStart = selection.range.start
    unless rangeStart?
      throw new Error "Called getTextQuoteSelector() on a range with no valid start."
    rangeEnd = selection.range.end
    unless rangeEnd?
      throw new Error "Called getTextQuoteSelector() on a range with no valid end."

    if document.getStartPosForNode?
      # Calculate the quote and context using DTM

      startOffset = document.getStartPosForNode rangeStart
      endOffset = document.getEndPosForNode rangeEnd

      if startOffset? and endOffset?
        quote = document.getCorpus()[startOffset .. endOffset-1].trim()
        [prefix, suffix] = document.getContextForCharRange startOffset, endOffset

        [
          type: "TextQuoteSelector"
          exact: quote
          prefix: prefix
          suffix: suffix
        ]
      else
        # It looks like we can't determine the start and end offsets.
        # That means no valid TextQuote selector can be generated from this.
        console.log "Warning: can't generate TextQuote selector.", startOffset, endOffset
        [ ]
    else
      # Get the quote directly from the range
      [
        type: "TextQuoteSelector"
        exact: selection.range.text().trim()
      ]

