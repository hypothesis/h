# Text search library
class window.DomTextMatcher
  constructor: (@corpus) ->

  # Search for text using exact string matching
  #
  # Parameters:
  #  pattern: what to search for
  #
  #  distinct: forbid overlapping matches? (defaults to true)
  #
  #  caseSensitive: should the search be case sensitive? (defaults to false)
  # 
  # 
  # For the details about the returned data structure,
  # see the documentation of the search() method.
  searchExact: (pattern, distinct = true, caseSensitive = false) ->
    if not @pm then @pm = new window.DTM_ExactMatcher
    @pm.setDistinct(distinct)
    @pm.setCaseSensitive(caseSensitive)
    @_search @pm, pattern

  # Search for text using regular expressions
  #
  # Parameters:
  #  pattern: what to search for
  #
  #  caseSensitive: should the search be case sensitive? (defaults to false)
  # 
  # For the details about the returned data structure,
  # see the documentation of the search() method.
  searchRegex: (pattern, caseSensitive = false) ->
    if not @rm then @rm = new window.DTM_RegexMatcher
    @rm.setCaseSensitive(caseSensitive)
    @_search @rm, pattern

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
  # For the details about the returned data structure,
  # see the documentation of the search() method.
  searchFuzzy: (pattern, pos, caseSensitive = false, options = {}) ->
    @ensureDMP()
    @dmp.setMatchDistance options.matchDistance ? 1000
    @dmp.setMatchThreshold options.matchThreshold ? 0.5
    @dmp.setCaseSensitive caseSensitive
    @_search @dmp, pattern, pos, options

  searchFuzzyWithContext: (prefix, suffix, pattern, expectedStart = null, expectedEnd = null, caseSensitive = false, options = {}) ->
    @ensureDMP()

    # No context, to joy
    unless (prefix? and suffix?)
      throw new Error "Can not do a context-based fuzzy search
 with missing context!"

    # Get full document length
    len = @corpus().length

    # Get a starting position for the prefix search
    expectedPrefixStart = if expectedStart?
      expectedStart - prefix.length
    else
      len / 2

    # Do the fuzzy search for the prefix
    @dmp.setMatchDistance options.contextMatchDistance ? len * 2
    @dmp.setMatchThreshold options.contextMatchThreshold ? 0.5
    prefixResult = @dmp.search @corpus(), prefix, expectedPrefixStart

    # If the prefix is not found, give up
    unless prefixResult.length then return matches: []

    # This is where the prefix was found
    prefixStart = prefixResult[0].start
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
    remainingText = @corpus().substr prefixEnd

    # Calculate expected position
    expectedSuffixStart = patternLength

    # Do the fuzzy search for the suffix
    suffixResult = @dmp.search remainingText, suffix, expectedSuffixStart

    # If the suffix is not found, give up
    unless suffixResult.length then return matches: []

    # This is where the suffix was found
    suffixStart = prefixEnd + suffixResult[0].start
    suffixEnd = prefixEnd + suffixResult[0].end

    # This if the range between the prefix and the suffix
    charRange =
      start: prefixEnd
      end: suffixStart

    # Get the configured threshold for the pattern matching
    matchThreshold = options.patternMatchThreshold ? 0.5

    # See how good a match we have
    analysis = @_analyzeMatch pattern, charRange, true

    # Should we try to find a better match by moving the
    # initial match around a little bit, even if this has
    # a negative impact on the similarity of the context?
    if pattern? and options.flexContext and not analysis.exact
      # Do we have and exact match for the quote around here?

      if not @pm then @pm = new window.DTM_ExactMatcher
      @pm.setDistinct false
      @pm.setCaseSensitive false

      flexMatches = @pm.search @corpus()[prefixStart..suffixEnd], pattern
      delete candidate
      bestError = 2

      for flexMatch in flexMatches

        # Calculate the range that matched the quote
        flexRange =
          start: prefixStart + flexMatch.start
          end: prefixStart + flexMatch.end

        # Check how the prefix would fare
        prefixRange = start: prefixStart, end: flexRange.start
        a1 = @_analyzeMatch prefix, prefixRange, true
        prefixError = if a1.exact then 0 else a1.comparison.errorLevel

        # Check how the suffix would fare
        suffixRange = start: flexRange.end, end: suffixEnd
        a2 = @_analyzeMatch suffix, suffixRange, true
        suffixError = if a2.exact then 0 else a2.comparison.errorLevel

        # Did we at least one match?
        if a1.exact or a2.exact
          # Yes, we did. Calculate the total error
          totalError = prefixError + suffixError

          # Is this better than our best bet?
          if totalError < bestError
            # This is our best candidate so far. Store it.
            candidate = flexRange
            bestError = totalError

      if candidate?
        console.log "flexContext adjustment: we found a better candidate!"
        charRange = candidate
        analysis = @_analyzeMatch pattern, charRange, true

    # Do we have to compare what we found to a pattern?
    if (not pattern?) or # "No pattern, nothing to compare. Assume it's OK."
        analysis.exact or # "Found text matches exactly to pattern"
        (analysis.comparison.errorLevel <= matchThreshold) # still acceptable

      # Collect the results
      match = {}
      for obj in [charRange, analysis]
        for k, v of obj
          match[k] = v
      return matches: [match]

#    console.log "Rejecting the match, because error level is too high. (" +
#        errorLevel + ")"
    return matches: []

  # ===== Private methods (never call from outside the module) =======

  # Do some normalization to get a "canonical" form of a string.
  # Used to even out some browser differences.  
  _normalizeString: (string) -> (string.replace /\s{2,}/g, " ").trim()

  # Search for text with a custom matcher object
  #
  # Parameters:
  #  matcher: the object to use for doing the plain-text part of the search
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
  _search: (matcher, pattern, pos, options = {}) ->
    # Prepare and check the pattern 
    unless pattern? then throw new Error "Can't search for null pattern!"
    pattern = pattern.trim()
    unless pattern? then throw new Error "Can't search an for empty pattern!"

    fuzzyComparison = options.withFuzzyComparison ? false

    t1 = @timestamp()

    # Do the text search
    textMatches = matcher.search @corpus(), pattern, pos, options
    t2 = @timestamp()

    matches = []
    for textMatch in textMatches
      do (textMatch) =>
        # See how good a match we have
        analysis = @_analyzeMatch pattern, textMatch, fuzzyComparison
        
        # Collect the results
        match = {}
        for obj in [textMatch, analysis]
          for k, v of obj
            match[k] = v
        
        matches.push match
        null
    t3 = @timestamp()
    result = 
      matches: matches
      time:
        phase1_textMatching: t2 - t1
        phase2_matchMapping: t3 - t2
        total: t3 - t1
    result

  timestamp: -> new Date().getTime()

  # Read a match returned by the matcher engine, and compare it with the pattern
  _analyzeMatch: (pattern, charRange, useFuzzy = false) ->
    expected = @_normalizeString pattern
    found = @_normalizeString @corpus()[charRange.start .. charRange.end - 1]
    result =
      found: found
      exact: found is expected

    # If the match is not exact, check whether the changes are
    # only case differences
    unless result.exact then result.exactExceptCase =
      expected.toLowerCase() is found.toLowerCase()

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
