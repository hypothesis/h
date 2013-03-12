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
  # The usage of this feature is not mandatorry; if not receiving change notifications,
  # the library will just assume that the document can change anythime, and therefore
  # will not assume any stability.
  documentChanged: -> @mapper.documentChanged()

  # The available paths which can be searched
  #
  # An map is returned, where the keys are the paths, and the values are objects with the following fields:
  #   path: the valid path value
  #   node: reference to the DOM node
  #   content: the text content of the node, as rendered by the browser
  #   length: the length of the next content
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
  # For the details about the returned data structure, see the documentation of the search() method.
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
  # For the details about the returned data structure, see the documentation of the search() method.
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
  #     fine-tuning parameters for the d-m-p library.
  #     See http://code.google.com/p/google-diff-match-patch/wiki/API for details.
  # 
  #  path: the sub-tree inside the DOM you want to search.
  #    Must be an XPath expression, relative to the configured root node.
  #    You can check for valid input values using the getAllPaths method above.
  #    It's not necessary to submit path, if the search was prepared beforehand,
  #    with the prepareSearch() method
  # 
  # For the details about the returned data structure, see the documentation of the search() method.
  searchFuzzy: (pattern, pos, caseSensitive = false, path = null, options = {}) ->
    unless @dmp?
      unless window.DTM_DMPMatcher?
        throw new Error "DTM_DMPMatcher is not available. Have you loaded the text match engines?"
      @dmp = new window.DTM_DMPMatcher
    @dmp.setMatchDistance options.matchDistance ? 1000
    @dmp.setMatchThreshold options.matchThreshold ? 0.5
    @dmp.setCaseSensitive caseSensitive
    @search @dmp, pattern, pos, path, options

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
  # , each element with "start", "end", "found" and "nodes" fields.
  # start and end specify where the pattern was found; "found" is the matching slice.
  # Nodes is the list of matching nodes, with details about the matches.
  # 
  # If no match is found, null is returned.  # 
  search: (matcher, pattern, pos, path = null, options = {}) ->
    # Prepare and check the pattern 
    unless pattern? then throw new Error "Can't search for null pattern!"
    pattern = pattern.trim()
    unless pattern? then throw new Error "Can't search an for empty pattern!"

    # Do some preparation, if required
    t0 = @timestamp()
    if path? then @scan()
    t1 = @timestamp()

    # Check preparations    
    unless @mapper.corpus? then throw new Error "Not prepared to search! (call PrepareSearch, or pass me a path)"

    # Do the text search
    textMatches = matcher.search @mapper.corpus, pattern, pos, options
    t2 = @timestamp()

    # Collect the mappings

    # Should work like a comprehension, but  it does not. WIll fix later.
    # matches = ($.extend {}, match, @mapper.getMappingsFor match.start, match.end) for match in textMatches

    matches = []
    for match in textMatches
      do (match) =>
        analysis = @analyzeMatch pattern, match
        mappings = @mapper.getMappingsForCharRange match.start, match.end
        newMatch = $.extend {}, match, analysis, mappings
        matches.push newMatch
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

  # Read a match returned by the matcher engine, and compare it with the pattern.
  analyzeMatch: (pattern, match) ->
    found = @mapper.corpus.substr match.start, match.end-match.start
    result =
      found: found
      exact: found is pattern

