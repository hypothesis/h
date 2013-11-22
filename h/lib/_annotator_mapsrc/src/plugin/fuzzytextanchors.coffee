# Annotator plugin for fuzzy text matching
class Annotator.Plugin.FuzzyTextAnchors extends Annotator.Plugin

  pluginInit: ->
    # Do we have the basic text anchors plugin loaded?
    unless @annotator.plugins.TextAnchors
      throw "The FuzzyTextAnchors Annotator plugin requires the TextAnchors plugin."
    unless @annotator.plugins.DomTextMapper
      throw "The FuzzyTextAnchors Annotator plugin requires the DomTextMapper plugin."

    # Initialize the text matcher library
    @textFinder = new DomTextMatcher => @annotator.domMapper.getCorpus()

    # Register our fuzzy strategies
    @annotator.anchoringStrategies.push
      # Two-phased fuzzy text matching strategy. (Using context and quote.)
      # This can handle document structure changes,
      # and also content changes.
      name: "two-phase fuzzy"
      code: this.twoPhaseFuzzyMatching

    @annotator.anchoringStrategies.push
      # Naive fuzzy text matching strategy. (Using only the quote.)
      # This can handle document structure changes,
      # and also content changes.
      name: "one-phase fuzzy"
      code: this.fuzzyMatching

  twoPhaseFuzzyMatching: (annotation, target) =>
    # Fetch the quote and the context
    quoteSelector = @annotator.findSelector target.selector, "TextQuoteSelector"
    prefix = quoteSelector?.prefix
    suffix = quoteSelector?.suffix
    quote = quoteSelector?.exact

    # No context, to joy
    unless (prefix? and suffix?) then return null

    # Fetch the expected start and end positions
    posSelector = @annotator.findSelector target.selector, "TextPositionSelector"
    expectedStart = posSelector?.start
    expectedEnd = posSelector?.end

    options =
      contextMatchDistance: @annotator.domMapper.getCorpus().length * 2
      contextMatchThreshold: 0.5
      patternMatchThreshold: 0.5
      flexContext: true
    result = @textFinder.searchFuzzyWithContext prefix, suffix, quote,
      expectedStart, expectedEnd, false, options

    # If we did not got a result, give up
    unless result.matches.length
 #     console.log "Fuzzy matching did not return any results. Giving up on two-phase strategy."
      return null

    # here is our result
    match = result.matches[0]
#    console.log "2-phase fuzzy found match at: [" + match.start + ":" +
#      match.end + "]: '" + match.found + "' (exact: " + match.exact + ")"

    # OK, we have everything
    # Create a TextPositionAnchor from this data
    new @annotator.TextPositionAnchor @annotator, annotation, target,
      match.start, match.end,
      (@annotator.domMapper.getPageIndexForPos match.start),
      (@annotator.domMapper.getPageIndexForPos match.end),
      match.found,
      unless match.exact then match.comparison.diffHTML,
      unless match.exact then match.exactExceptCase

  fuzzyMatching: (annotation, target) =>
    # Fetch the quote
    quoteSelector = @annotator.findSelector target.selector, "TextQuoteSelector"
    quote = quoteSelector?.exact

    # No quote, no joy
    unless quote? then return null

    # For too short quotes, this strategy is bound to return false positives.
    # See https://github.com/hypothesis/h/issues/853 for details.
    return unless quote.length >= 32

    # Get a starting position for the search
    posSelector = @annotator.findSelector target.selector, "TextPositionSelector"
    expectedStart = posSelector?.start

    # Get full document length
    len = @annotator.domMapper.getCorpus().length

    # If we don't have the position saved, start at the middle of the doc
    expectedStart ?= len / 2

    # Do the fuzzy search
    options =
      matchDistance: len * 2
      withFuzzyComparison: true
    result = @textFinder.searchFuzzy quote, expectedStart, false, options

    # If we did not got a result, give up
    unless result.matches.length
#      console.log "Fuzzy matching did not return any results. Giving up on one-phase strategy."
      return null

    # here is our result
    match = result.matches[0]
#    console.log "1-phase fuzzy found match at: [" + match.start + ":" +
#      match.end + "]: '" + match.found + "' (exact: " + match.exact + ")"

    # OK, we have everything
    # Create a TextPosutionAnchor from this data
    new @annotator.TextPositionAnchor @annotator, annotation, target,
      match.start, match.end,
      (@annotator.domMapper.getPageIndexForPos match.start),
      (@annotator.domMapper.getPageIndexForPos match.end),
      match.found,
      unless match.exact then match.comparison.diffHTML,
      unless match.exact then match.exactExceptCase

