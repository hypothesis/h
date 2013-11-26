# Naive text matcher 
class window.DTM_ExactMatcher
  constructor: ->
    @distinct = true
    @caseSensitive = false  
 
  setDistinct: (value) -> @distinct = value

  setCaseSensitive: (value) -> @caseSensitive = value
        
  search: (text, pattern) ->
#    console.log "Searching for '" + pattern + "' in '" + text + "'."
    pLen = pattern.length
    results = []
    index = 0
    unless @caseSensitive
      text = text.toLowerCase()
      pattern = pattern.toLowerCase()
    while (i = text.indexOf pattern) > -1
      do =>
#        console.log "Found '" + pattern + "' @ " + i +
#            " (=" + (index + i) + ")"
        results.push
          start: index + i
          end: index + i + pLen
        if @distinct
          text = text.substr i + pLen
          index += i + pLen
        else
          text = text.substr i + 1
          index += i + 1

    results

class window.DTM_RegexMatcher
  constructor: ->
    @caseSensitive = false  
 
  setCaseSensitive: (value) -> @caseSensitive = value

  search: (text, pattern) ->
    re = new RegExp pattern, if @caseSensitive then "g" else "gi"
    { start: m.index, end: m.index + m[0].length } while m = re.exec text
                
# diff-match-patch - based text matcher 
class window.DTM_DMPMatcher
  constructor: ->
     @dmp = new diff_match_patch
     @dmp.Diff_Timeout = 0
     @caseSensitive = false

  _reverse: (text) -> text.split("").reverse().join ""

  # Use this to get the max allowed pattern length.
  # Trying to use a longer pattern will give an error.
  getMaxPatternLength: -> @dmp.Match_MaxBits

  # The following example is a classic dilemma.
  # There are two potential matches, one is close to the expected location
  # but contains a one character error, the other is far from the expected
  # location but is exactly the pattern sought after:
  # 
  # match_main("abc12345678901234567890abbc", "abc", 26)
  # 
  # Which result is returned (0 or 24) is determined by the
  # MatchDistance property.
  # 
  # An exact letter match which is 'distance' characters away
  # from the fuzzy location would score as a complete mismatch.
  # For example, a distance of '0' requires the match be at the exact
  # location specified, whereas a threshold of '1000' would require
  # a perfect match to be within 800 characters of the expected location
  # to be found using a 0.8 threshold (see below).
  #
  # The larger MatchDistance is, the slower search may take to compute.
  # 
  # This variable defaults to 1000.
  setMatchDistance: (distance) -> @dmp.Match_Distance = distance
  getMatchDistance: -> @dmp.Match_Distance

  # MatchThreshold determines the cut-off value for a valid match.
  #  
  # If Match_Threshold is closer to 0, the requirements for accuracy
  # increase. If Match_Threshold is closer to 1 then it is more likely
  # that a match will be found. The larger Match_Threshold is, the slower
  # search may take to compute.
  # 
  # This variable defaults to 0.5.
  setMatchThreshold: (threshold) -> @dmp.Match_Threshold = threshold
  getMatchThreshold: -> @dmp.Match_Threshold

  getCaseSensitive: -> caseSensitive
  setCaseSensitive: (value) -> @caseSensitive = value

  # Given a text to search, a pattern to search for and an
  # expected location in the text near which to find the pattern,
  # return the location which matches closest.
  # 
  # The function will search for the best match based on both the number
  # of character errors between the pattern and the potential match,
  # as well as the distance between the expected location and the
  # potential match.
  #
  # If no match is found, the function returns null.
  search: (text, pattern, expectedStartLoc = 0, options = {}) ->
#    console.log "In dtm search. text: '" + text + "', pattern: '" + pattern +
#       "', expectedStartLoc: " + expectedStartLoc + ", options:"
#    console.log options
    if expectedStartLoc < 0
      throw new Error "Can't search at negative indices!"
    if expectedStartLoc isnt Math.floor expectedStartLoc
      throw new Error "Expected start location must be an integer."

    unless @caseSensitive
      text = text.toLowerCase()
      pattern = pattern.toLowerCase()

    pLen = pattern.length
    maxLen = @getMaxPatternLength()

    if pLen <= maxLen
      result = @searchForSlice text, pattern, expectedStartLoc
    else
      startSlice = pattern.substr 0, maxLen
      startPos = @searchForSlice text, startSlice, expectedStartLoc
      if startPos?
        startLen = startPos.end - startPos.start
        endSlice = pattern.substr pLen - maxLen, maxLen
        endLoc = startPos.start + pLen - maxLen
        endPos = @searchForSlice text, endSlice, endLoc
        if endPos?
          endLen = endPos.end - endPos.start
          matchLen = endPos.end - startPos.start
          startIndex = startPos.start
          endIndex = endPos.end
        
          if pLen*0.5 <= matchLen <= pLen*1.5
            result =
              start: startIndex
              end: endPos.end
#              data: 
#                startError: startPos.data.error
#                endError: endPos.data.error
#                uncheckedMidSection: Math.max 0, matchLen - startLen - endLen
#                lengthError: matchLen - pLen
#          else
#            console.log "Sorry, matchLen (" + matchLen + ") is not between " +
#                0.5*pLen + " and " + 1.5*pLen
#        else
#          console.log "endSlice ('" + endSlice + "') not found"
#      else
#        console.log "startSlice ('" + startSlice + "') not found"

    unless result? then return []

    if options.withLevenhstein or options.withDiff
      found = text.substr result.start, result.end - result.start
      result.diff = @dmp.diff_main pattern, found
      if options.withLevenshstein
        result.lev = @dmp.diff_levenshtein result.diff
      if options.withDiff
        @dmp.diff_cleanupSemantic result.diff
        result.diffHTML = @dmp.diff_prettyHtml result.diff

    [result]

  # Compare two string slices, get Levenhstein and visual diff
  compare: (text1, text2) ->
    unless (text1? and text2?)
      throw new Error "Can not compare non-existing strings!"
    result = {}
    result.diff = @dmp.diff_main text1, text2
    result.lev = @dmp.diff_levenshtein result.diff
    result.errorLevel = result.lev / text1.length
    @dmp.diff_cleanupSemantic result.diff
    result.diffHTML = @dmp.diff_prettyHtml result.diff
    result


  # ============= Private part ==========================================
  # You don't need to call the functions below this point manually

  searchForSlice: (text, slice, expectedStartLoc) ->
#    console.log "searchForSlice: '" + text + "', '" + slice + "', " +
#        expectedStartLoc

    r1 = @dmp.match_main text, slice, expectedStartLoc
    startIndex = r1.index
    if startIndex is -1 then return null
        
    txet = @_reverse text
    nrettap = @_reverse slice
    expectedEndLoc = startIndex + slice.length
    expectedDneLoc = text.length - expectedEndLoc
    r2 = @dmp.match_main txet, nrettap, expectedDneLoc
    dneIndex = r2.index
    endIndex = text.length - dneIndex

    result =
      start: startIndex
      end: endIndex
