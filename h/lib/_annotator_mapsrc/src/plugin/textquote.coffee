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

    [
      if @annotator.plugins.DomTextMapper
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
        exact: selection.range.text().trim()

    ]


