class window.DomTextMatcher

  # ===== Public methods =======

  # Consider only the sub-tree beginning with the given node.
  # 
  # This will be the root node to use for all operations.
  setRootNode: (rootNode) -> @mapper.setRootNode rootNode

  # Consider only the sub-tree beginning with the node whose ID was given.
  # 
  # This will be the root node to use for all operations.
  setRootId: (rootId) -> @mapper.setRootId rootId

  # Use this iframe for operations.
  #
  # Call this when mapping content in an iframe.
  setRootIframe: (iframeId) -> @mapper.setRootIframe iframeId
        
  # Work with the whole DOM tree
  # 
  # (This is the default; you only need to call this, if you have configured
  # a different root earlier, and now you want to restore the default setting.)
  setRealRoot: -> @mapper.setRealRoot()

  # Notify the library that the document has changed.
  # This means that subsequent calls can not safely re-use previously cached
  # data structures, so some calculations will be necessary again.
  #
  # The usage of this feature is not mandatorry; if not receiving change
  # notifications, the library will just assume that the document can change
  # anythime, and therefore will not assume any stability.
  documentChanged: -> @mapper.documentChanged()

  # The available paths which can be searched
  #
  # An map is returned, where the keys are the paths, and the values hold
  # the collected informatino about the given sub-trees of the DOM.
  scan: ->
    t0 = @timestamp()
    data = @mapper.scan()
    t1 = @timestamp()
    return time: t1 - t0, data: data

  # Return the default path
  getDefaultPath: -> @mapper.getDefaultPath()

  # Search for text using exact string matching
  #
  # Parameters:
  #  pattern: what to search for
  #
  #  distinct: forbid overlapping matches? (defaults to true)
  #
  #  caseSensitive: should the search be case sensitive? (defaults to false)
  # 
  #  path: the sub-tree inside the DOM you want to search.
  #    Must be an XPath expression, relative to the configured root node.
  #    You can check for valid input values using the getAllPaths method above.
  #    It's not necessary to submit path, if the search was prepared beforehand,
  #    with the prepareSearch() method
  # 
  # For the details about the returned data structure,
  # see the documentation of the search() method.
  searchExact: (pattern, distinct = true, caseSensitive = false, path = null) ->
    if not @pm then @pm = new window.DTM_ExactMatcher
    @pm.setDistinct(distinct)
    @pm.setCaseSensitive(caseSensitive)
    @search @pm, pattern, null, path

  # Search for text using regular expressions
  #
  # Parameters:
  #  pattern: what to search for
  #
  #  caseSensitive: should the search be case sensitive? (defaults to false)
  # 
  #  path: the sub-tree inside the DOM you want to search.
  #    Must be an XPath expression, relative to the configured root node.
  #    You can check for valid input values using the getAllPaths method above.
  #    It's not necessary to submit path, if the search was prepared beforehand,
  #    with the prepareSearch() method
  # 
  # For the details about the returned data structure,
  # see the documentation of the search() method.
  searchRegex: (pattern, caseSensitive = false, path = null) ->
    if not @rm then @rm = new window.DTM_RegexMatcher
    @rm.setCaseSensitive(caseSensitive)
    @search @rm, pattern, null, path

  # Search for text using fuzzy text matching
  #
  # Parameters:
  #  pattern: what to search for
  #
  #  pos: where to start searching
  #
  #  caseSensitive: should the search be case sensitive? (defaults to false)
  # 
  #  matchDistance and
  #  matchThreshold:
  #   fine-tuning parameters for the d-m-p library.
  #   See http://code.google.com/p/google-diff-match-patch/wiki/API for details.
  # 
  #  path: the sub-tree inside the DOM you want to search.
  #    Must be an XPath expression, relative to the configured root node.
  #    You can check for valid input values using the getAllPaths method above.
  #    It's not necessary to submit path, if the search was prepared beforehand,
  #    with the prepareSearch() method
  # 
  # For the details about the returned data structure,
  # see the documentation of the search() method.
  searchFuzzy: (pattern, pos, caseSensitive = false, path = null, options = {}) ->
    @ensureDMP()
    @dmp.setMatchDistance options.matchDistance ? 1000
    @dmp.setMatchThreshold options.matchThreshold ? 0.5
    @dmp.setCaseSensitive caseSensitive
    @search @dmp, pattern, pos, path, options

  # Do some normalization to get a "canonical" form of a string.
  # Used to even out some browser differences.  
  normalizeString: (string) -> string.replace /\s{2,}/g, " "

  searchFuzzyWithContext: (prefix, suffix, pattern, expectedStart = null, expectedEnd = null, caseSensitive = false, path = null, options = {}) ->
    @ensureDMP()

    # No context, to joy
    unless (prefix? and suffix?)
      throw new Error "Can not do a context-based fuzzy search
 with missing context!"

    # Get full document length
    len = @mapper.getDocLength()

    # Get a starting position for the prefix search
    expectedPrefixStart = if expectedStart?
      expectedStart - prefix.length
    else
      len / 2

    # Do the fuzzy search for the prefix
    @dmp.setMatchDistance options.contextMatchDistance ? len * 2
    @dmp.setMatchThreshold options.contextMatchThreshold ? 0.5
    prefixResult = @dmp.search @mapper.corpus, prefix, expectedPrefixStart

    # If the prefix is not found, give up
    unless prefixResult.length then return matches: []

    # This is where the prefix ends
    prefixEnd = prefixResult[0].end

    # Let's find out where do we expect to find the suffix!
    # We need the pattern's length.
    patternLength = if pattern?
      # If we have a pattern, use it's length
      pattern.length
    else if expectedStart? and expectedEnd? 
      # We don't have a pattern, but at least
      # have valid expectedStart and expectedEnd values,
      # get a length from that.
      expectedEnd - expectedStart
    else 
      # We have no idea about where the suffix could be.
      # Let's just pull a number out of ... thin air.
      64

    # Get the part of text that is after the prefix
    remainingText = @mapper.corpus.substr prefixEnd

    # Calculate expected position
    expectedSuffixStart = patternLength

    # Do the fuzzy search for the suffix
    suffixResult = @dmp.search remainingText, suffix, expectedSuffixStart

    # If the suffix is not found, give up
    unless suffixResult.length then return matches: []

    # This is where the suffix starts
    suffixStart = prefixEnd + suffixResult[0].start

    charRange =
      start: prefixEnd
      end: suffixStart

    # Get the configured threshold for the pattern matching
    matchThreshold = options.patternMatchThreshold ? 0.5

    # See how good a match we have
    analysis = @analyzeMatch pattern, charRange, true

    # Do we have to compare what we found to a pattern?
    if (not pattern?) or # "No pattern, nothing to compare. Assume it's OK."
        analysis.exact or # "Found text matches exactly to pattern"
        (analysis.comparison.errorLevel <= matchThreshold) # still acceptable
      mappings = @mapper.getMappingsForCharRange prefixEnd, suffixStart

      # Collect the results
      match = {}
      for obj in [charRange, analysis, mappings]
        for k, v of obj
          match[k] = v
      return matches: [match]

#    console.log "Rejecting the match, because error level is too high. (" +
#        errorLevel + ")"
    return matches: []


  # ===== Private methods (never call from outside the module) =======

  constructor: (domTextMapper) ->
    @mapper = domTextMapper

  # Search for text with a custom matcher object
  #
  # Parameters:
  #  matcher: the object to use for doing the plain-text part of the search
  #  path: the sub-tree inside the DOM you want to search.
  #    Must be an XPath expression, relative to the configured root node.
  #    You can check for valid input values using the getAllPaths method above.
  #  pattern: what to search for
  #  pos: where do we expect to find it
  #
  # A list of matches is returned.
  # 
  # Each match has "start", "end", "found" and "nodes" fields.
  # start and end specify where the pattern was found;
  # "found" is the matching slice.
  # Nodes is the list of matching nodes, with details about the matches.
  # 
  # If no match is found, an empty list is returned.
  search: (matcher, pattern, pos, path = null, options = {}) ->
    # Prepare and check the pattern 
    unless pattern? then throw new Error "Can't search for null pattern!"
    pattern = pattern.trim()
    unless pattern? then throw new Error "Can't search an for empty pattern!"

    fuzzyComparison = options.withFuzzyComparison ? false

    # Do some preparation, if required
    t0 = @timestamp()
    if path? then @scan()
    t1 = @timestamp()

    # Do the text search
    textMatches = matcher.search @mapper.corpus, pattern, pos, options
    t2 = @timestamp()

    matches = []
    for textMatch in textMatches
      do (textMatch) =>
        # See how good a match we have        
        analysis = @analyzeMatch pattern, textMatch, fuzzyComparison
        
        # Collect the mappings        
        mappings = @mapper.getMappingsForCharRange textMatch.start,
            textMatch.end

        # Collect the results
        match = {}
        for obj in [textMatch, analysis, mappings]
          for k, v of obj
            match[k] = v
        
        matches.push match
        null
    t3 = @timestamp()
    result = 
      matches: matches
      time:
        phase0_domMapping: t1 - t0
        phase1_textMatching: t2 - t1
        phase2_matchMapping: t3 - t2
        total: t3 - t0
    result

  timestamp: -> new Date().getTime()

  # Read a match returned by the matcher engine, and compare it with the pattern
  analyzeMatch: (pattern, charRange, useFuzzy = false) ->
    expected = @normalizeString pattern        
    found = @normalizeString @mapper.getContentForCharRange charRange.start,
        charRange.end
    result =
      found: found
      exact: found is expected

    # if we are interested in fuzzy comparison, calculate that, too
    if not result.exact and useFuzzy
      @ensureDMP()
      result.comparison = @dmp.compare expected, found

    result

  ensureDMP: ->
    unless @dmp?
      unless window.DTM_DMPMatcher?
        throw new Error "DTM_DMPMatcher is not available.
 Have you loaded the text match engines?"
      @dmp = new window.DTM_DMPMatcher