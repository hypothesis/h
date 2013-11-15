# Common functions for all page-based document mapper modules
class window.PageTextMapperCore

  CONTEXT_LEN: 32

  # Get the page index for a given character position
  getPageIndexForPos: (pos) ->
    for info in @pageInfo
      if info.start <= pos < info.end
        return info.index
        console.log "Not on page " + info.index
    return -1

  # A new page was rendered
  _onPageRendered: (index) =>
    #console.log "Allegedly rendered page #" + index

    # Is it really rendered?
    unless @_isPageRendered index
    #console.log "Page #" + index + " is not really rendered yet."
      setTimeout (=> @_onPageRendered index), 1000
      return

    # Collect info about the new DOM subtree
    @_mapPage @pageInfo[index]

  # Determine whether a given page has been rendered and mapped
  isPageMapped: (index) ->
    return @pageInfo[index]?.domMapper?

   # Create the mappings for a given page    
  _mapPage: (info) ->
    info.node = @getRootNodeForPage info.index        
    info.domMapper = new DomTextMapper("d-t-m for page #" + info.index)
    info.domMapper.setRootNode info.node
    info.domMapper.documentChanged()
    if @requiresSmartStringPadding
      info.domMapper.setExpectedContent info.content
    info.domMapper.scan()
    renderedContent = info.domMapper.getCorpus()
    if renderedContent isnt info.content
      console.log "Oops. Mismatch between rendered and extracted text, while mapping page #" + info.index + "!"
      console.trace()
      console.log "Rendered: " + renderedContent
      console.log "Extracted: " + info.content

    # Announce the newly available page
    setTimeout ->
      event = document.createEvent "UIEvents"
      event.initUIEvent "docPageMapped", false, false, window, 0
      event.pageIndex = info.index
      window.dispatchEvent event

  # Update the mappings for a given page
  _updateMap: (info) ->
    #console.log "Updating mappings for page #" + info.index
    info.domMapper.scan()

  # Delete the mappings for a given page
  _unmapPage: (info) ->
    delete info.domMapper

    # Announce the unavailable page
    event = document.createEvent "UIEvents"
    event.initUIEvent "docPageUnmapped", false, false, window, 0
    event.pageIndex = info.index
    window.dispatchEvent event

  # Announce scrolling
  _onScroll: ->
    event = document.createEvent "UIEvents"
    event.initUIEvent "docPageScrolling", false, false, window, 0
    window.dispatchEvent event

  # Look up info about a give DOM node, uniting page and node info
  getInfoForNode: (node) ->
    pageData = @getPageForNode node
    nodeData = pageData.domMapper.getInfoForNode node
    # Copy info about the node
    info = {}
    for k,v of nodeData
      info[k] = v
    # Correct the chatacter offsets with that of the page
    info.start += pageData.start
    info.end += pageData.start
    info.pageIndex = pageData.index
    info

  # Return some data about a given character range
  getMappingsForCharRange: (start, end, pages) ->
    #console.log "Get mappings for char range [" + start + "; " + end + "], for pages " + pages + "."

    # Check out which pages are these on
    startIndex = @getPageIndexForPos start
    endIndex = @getPageIndexForPos end
    #console.log "These are on pages [" + startIndex + ".." + endIndex + "]."

    # Function to get the relevant section inside a given page
    getSection = (index) =>
      info = @pageInfo[index]

      # Calculate in-page offsets
      realStart = (Math.max info.start, start) - info.start
      realEnd = (Math.min info.end, end) - info.start

      # Get the range inside the page
      mappings = info.domMapper.getMappingsForCharRange realStart, realEnd
      mappings.sections[0]

    # Get the section for all involved pages
    sections = {}
    for index in pages ? [startIndex..endIndex]
      sections[index] = getSection index

    # Return the data
    sections: sections

  getCorpus: -> @_corpus

  getContextForCharRange: (start, end) ->
    prefixStart = Math.max 0, start - @CONTEXT_LEN
    prefixLen = start - prefixStart
    prefix = @_corpus.substr prefixStart, prefixLen
    suffix = @_corpus.substr end, @CONTEXT_LEN
    [prefix.trim(), suffix.trim()]

  # Call this in scan, when you have the page contents
  _onHavePageContents: ->
    # Join all the text together
    @_corpus = (info.content for info in @pageInfo).join " "

    # Go over the pages, and calculate some basic info
    pos = 0
    @pageInfo.forEach (info, i) =>
      info.index = i
      info.len = info.content.length        
      info.start = pos
      info.end = (pos += info.len + 1)

  # Call this in scan, after resolving the promise  
  _onAfterScan: ->
    # Go over the pages again, and map the rendered ones
    @pageInfo.forEach (info, i) =>
      if @_isPageRendered i
        @_mapPage info
