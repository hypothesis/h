# This plugin defines the TextQuote selector
class Annotator.Plugin.TextQuote extends Annotator.Plugin

  @Annotator = Annotator
  @$ = Annotator.$

  # Plugin initialization
  pluginInit: ->

    # Register the creator for text quote selectors
    @annotator.selectorCreators.push
      name: "TextQuoteSelector"
      describe: @_getTextQuoteSelector

    # Register function to get quote from this selector
    @annotator.getQuoteForTarget = (target) =>
      selector = @annotator.findSelector target.selector, "TextQuoteSelector"
      if selector?
        @annotator.normalizeString selector.exact
      else
        null

  # Create a TextQuoteSelector around a range
  _getTextQuoteSelector: (selection) =>
    return [] unless selection.type is "text range"

    unless selection.range?
      throw new Error "Called getTextQuoteSelector() with null range!"

    rangeStart = selection.range.start
    unless rangeStart?
      throw new Error "Called getTextQuoteSelector() on a range with no valid start."
    rangeEnd = selection.range.end
    unless rangeEnd?
      throw new Error "Called getTextQuoteSelector() on a range with no valid end."

    if @annotator.domMapper.getStartPosForNode?
      # Calculate the quote and context using DTM

      startOffset = @annotator.domMapper.getStartPosForNode rangeStart
      endOffset = @annotator.domMapper.getEndPosForNode rangeEnd

      if startOffset? and endOffset?
        quote = @annotator.domMapper.getCorpus()[startOffset .. endOffset-1].trim()
        [prefix, suffix] = @annotator.domMapper.getContextForCharRange startOffset, endOffset

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


