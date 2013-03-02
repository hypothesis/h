class window.DomTextMapper

  USE_THEAD_TBODY_WORKAROUND = true
  USE_TABLE_TEXT_WORKAROUND = true
  CONTEXT_LEN = 32

  @instances: []

  @changed: (node, reason = "no reason") ->
    if @instances.length isnt 0
      dm = @instances[0]
      console.log "Node @ " + (dm.getPathTo node) + " has changed: '" + reason + "'."
    for instance in @instances
      instance.performUpdateOnNode node
    null

  constructor: ->
    this.setRealRoot()
    this.restrictToSerializable false
    window.DomTextMapper.instances.push this

  # ===== Public methods =======

  # Switch the library into "serializable-only" mode.
  # If set to true, all public API calls will be restricted to return
  # strictly serializable data structures.
  # (References to DOM objects will be omitted.)
  restrictToSerializable: (value = true) -> this.restricted = value

  # Consider only the sub-tree beginning with the given node.
  # 
  # This will be the root node to use for all operations.
  setRootNode: (rootNode) ->
    @rootWin = window     
    @pathStartNode = @rootNode = rootNode
#    console.log "Configured root node:"
#    console.log rootNode

  # Consider only the sub-tree beginning with the node whose ID was given.
  # 
  # This will be the root node to use for all operations.
  setRootId: (rootId) -> @setRootNode document.getElementById rootId

  # Use this iframe for operations.
  #
  # Call this when mapping content in an iframe.
  setRootIframe: (iframeId) ->
    iframe = window.document.getElementById iframeId
    unless iframe? then throw new Error "Can't find iframe with specified ID!"
    @rootWin = iframe.contentWindow
    unless @rootWin? then throw new Error "Can't access contents of the spefified iframe!"
    @rootNode = @rootWin.document
    @pathStartNode = @getBody()

  # Work with the whole DOM tree
  # 
  # (This is the default; you only need to call this, if you have configured
  # a different root earlier, and now you want to restore the default setting.)
  setRealRoot: ->
    @rootWin = window    
    @rootNode = document
    @pathStartNode = @getBody() 

  # Notify the library that the document has changed.
  # This means that subsequent calls can not safely re-use previously cached
  # data structures, so some calculations will be necessary again.
  #
  # The usage of this feature is not mandatorry; if not receiving change notifications,
  # the library will just assume that the document can change anythime, and therefore
  # will not assume any stability.
  documentChanged: ->
    @lastDOMChange = @timestamp()
#    console.log "Registered document change."

  # The available paths which can be scanned
  #
  # An map is returned, where the keys are the paths, and the values are objects with the following fields:
  #   path: the valid path value
  #   node: reference to the DOM node
  #   content: the text content of the node, as rendered by the browser
  #   length: the length of the next content
  getAllPaths: ->
#    console.log "in getAllPaths"
    if @domStableSince @lastCollectedPaths
      # We have a valid paths structure!
#      console.log "We have a valid DOM structure cache."
      return if @restricted then @cleanPaths else @allPaths

#    console.log "No valid cache, will have to calculate getAllPaths."
    startTime = @timestamp()
    @saveSelection()
    @allPaths = {}
    @collectPathsForNode @pathStartNode
    @restoreSelection()
    @lastCollectedPaths = @timestamp()
    console.log "Path traversal took " + (@lastCollectedPaths - startTime) + " ms."
    if @restricted
      @cleanPaths = {}
      for path, info of @allPaths
        cleanInfo = $.extend({}, info);
        delete cleanInfo.node
        @cleanPaths[path] = cleanInfo
      @cleanPaths
    else
      @allPaths

  # Return the default path
  getDefaultPath: -> @getPathTo @pathStartNode

  # Select the given path (for visual identification), and optionally scroll to it
  selectPath: (path, scroll = false) ->
    info = @allPaths[path]
    @selectNode info.node ? @lookUpNode info.path

  # Scan the given part of the document.
  # 
  # Creates  a list of mappings between the string indices
  # (as appearing in the displayed text) and the DOM elements.
  #
  # The "path" paremater specifies the sub-tree inside the DOM that should be scanned.
  # Must be an XPath expression, relative to the configured root node.
  # You can check for valid input values using the getAllPaths method above.
  #
  # If no path is given, the whole sub-tree is scanned,
  # starting with the configured root node.
  #
  # Nothing is returned; the following properties are populated:
  #
  #  mappings will contain the created mappings
  #  corpus will contain the text content of the selected path# 
  #  scannedPath will be set to the path
  scan: (path = null) ->
#    console.log "In scan"
    path ?= @getDefaultPath()
    if path is @scannedPath and @domStableSince @lastScanned
#      console.log "We have a valid cache. Returning instead of scanning."
      return
#    console.log "Scanning path: " + path
    @getAllPaths()
    node = @allPaths[path].node
    @mappings = {}
    @saveSelection()        
    @collectStrings node, path, null, 0, 0
    @restoreSelection()
    @scannedPath = path
    @lastScanned = @timestamp()
    @corpus = @mappings[path].pathInfo.content
#    console.log "Corpus is: " + @corpus
    null

  performUpdateOnNode: (node, escalating = false) ->
    unless node? then throw new Error "Called performUpdate with a null node!"
    unless @allPaths? then return #We don't have data yet. Not updating.
      
    startTime = @timestamp()
    unless escalating then @saveSelection()
    path = @getPathTo node
    pathInfo = @allPaths[path]
    unless pathInfo?
      @performUpdateOnNode node.parentNode, true
      unless escalating then @restoreSelection()        
      return
    console.log "Performing update on node @ path " + path
    unless @mappings[path]? then throw new error "Can not find mappings for path " + path
#    if escalating then console.log "(Escalated)"
#    console.log "Updating data about " + path + ": "
    if pathInfo.node is node and pathInfo.content is @getNodeContent node, false
#      console.log "Good, the node and the overall content is still the same"
#      console.log "Dropping obsolete path info and mappings for children..."
      prefix = path + "/"
      pathsToDrop =p

      # FIXME: There must be a more elegant way to do this. 
      pathsToDrop = []
      for p, data of @allPaths when @stringStartsWith p, prefix
        pathsToDrop.push p
      for p in pathsToDrop
        delete @mappings[p]
        delete @allPaths[p]        
        
#      console.log "Done. Collecting new path info..."
      @collectPathsForNode node

#      console.log "Done. Updating mappings..."

      if pathInfo.node is @pathStartNode
        console.log "Ended up rescanning the whole doc."
        @collectStrings node, path, null, 0, 0
      else
        parentPath = @parentPath path
        parentPathInfo = @allPaths[parentPath]
        unless parentPathInfo?
          throw new Error "While performing update on node " + path + ", no path info found for parent path: " + parentPath
        parentMappings = @mappings[parentPath]
        unless parentMappings?
          throw new Error "While performing update on node " + path + ", no mappings info found for parent path: " + parentPath
        oldIndex = @mappings[path].start - parentMappings.start
        @collectStrings node, path, parentPathInfo.content, parentMappings.start, oldIndex
        
#      console.log "Data update took " + (@timestamp() - startTime) + " ms."

    else
#      console.log "Uh-oh, the node has been replaced, or the overall content has changed!"
      if pathInfo.node isnt @pathStartNode
#        console.log "I guess I must go up one level."
        parentNode = if node.parentNode?
#          console.log "Node has parent, using that."
          node.parentNode
        else
          parentPath = @parentPath path
#          console.log "Node has no parent, will look up " + parentPath
          @lookUpNode parentPath
        @performUpdateOnNode parentNode, true
      else
        console.log "I can not go up, since I'm already at path start node. Barking out."
        throw new Error "Can not keep up with the changes, since even the node configured as path start node was replaced."
    unless escalating then @restoreSelection()        


  # Return the character range mappings for a given path in the DOM
  getRangeForPath: (path) ->
    result = @mappings[path]
    unless result? then throw new Error "Found no range for path '" + path + "'!"
    if @restricted
      result = $.extend {}, result;
      result.pathInfo = $.extend {}, result.pathInfo
      delete result.pathInfo.node
    result

  # Return the character range mappings for a given node in the DOM
  getMappingsForNode: (node) -> @getRangeForPath @getPathTo node

  # Get the matching DOM elements for a given set of text ranges
  # (Calles getMappingsForRange for each element in the givenl ist)
  getMappingsForRanges: (ranges, path = null) ->
#    console.log "Ranges:"
#    console.log ranges
    mappings = (for range in ranges
      mapping = @getMappingsForRange range.start, range.end, path
    )
#    console.log "Raw mappings:"
#    console.log mappings

    if @restricted
      mappings = (for mapping in mappings
        cleanMapping = $.extend {}, mapping
        delete cleanMapping.range
        cleanMapping.nodes = (for node in cleanMapping.nodes
          cleanNode = $.extend {}, node
          cleanNode.element = $.extend {}, cleanNode.element
          cleanNode.element.pathInfo = $.extend {}, cleanNode.element.pathInfo
          delete cleanNode.element.pathInfo.node
          cleanNode
        )
        cleanMapping
      )
#      console.log "Cleaned mappings:"
#      console.log mappings

    mappings

  getContentForPath: (path = null) -> 
    path ?= @getDefaultPath()       
    @allPaths[path].content

  getLengthForPath: (path = null) ->
    path ?= @getDefaultPath()
    @allPaths[path].length

  getContentForRange: (start, end, path = null) ->
    @getContentForPath(path).substr start, end - start

  # Get the context that encompasses the given text range
  getContextForRange: (start, end) ->
    content = @getContentForPath()
    prefixStart = Math.max 0, start - CONTEXT_LEN
    prefixLen = start - prefixStart
    prefix = content.substr prefixStart, prefixLen
    suffix = content.substr end, prefixLen
    [prefix.trim(), suffix.trim()]
        

  # Get the matching DOM elements for a given text range
  # 
  # If the "path" argument is supplied, scan is called automatically.
  # (Except if the supplied path is the same as the last scanned path.)
  getMappingsForRange: (start, end, path = null) ->
    unless (start? and end?) then throw new Error "start and end is required!"    
#    console.log "Collecting matches for [" + start + ":" + end + "]"
    if path? then @scan path

    unless @scannedPath? then throw new Error "Can not run getMappingsFor() without existing mappings. Either supply a path to scan, or call scan() beforehand!"

    # Collect the matching mappings
#    console.log "Collecting mappings"
    matches = []
    for p, mapping of @mappings when mapping.atomic and @regions_overlap mapping.start, mapping.end, start, end
      do (mapping) =>
#        console.log "Checking " + mapping.pathInfo.path
#        console.log mapping
        match =
          element: mapping
        full_match = start <= mapping.start and mapping.end <= end
        if full_match 
          match.full = true
          match.wanted = mapping.content
        else
         if start <= mapping.start
            match.end = end - mapping.start
            match.wanted = mapping.pathInfo.content.substr 0, match.end                
          else if mapping.end <= end
            match.start = start - mapping.start
            match.wanted = mapping.pathInfo.content.substr match.start        
          else
            match.start = start - mapping.start
            match.end = end - mapping.start
            match.wanted = mapping.pathInfo.content.substr match.start, match.end - match.start
        
        @computeSourcePositions match
        match.yields = mapping.pathInfo.node.data.substr match.startCorrected, match.endCorrected - match.startCorrected
        matches.push match
#        console.log "Done with " + mapping.pathInfo.path

    if matches.length is 0
#      console.log "Wanted: [" + start + ":" + end + "], found: "
#      f = ((start: mapping.start, end: mapping.end) for p, mapping of @mappings when mapping.atomic)
#      console.log f
#      console.log "[" + mapping.start + ":" + mapping.end + "]" for p, mapping of @mappings when mapping.atomic
      throw new Error "No matches found for [" + start + ":" + end + "]!"

        
    # Create a DOM range object
#    console.log "Building range..."
    r = @rootWin.document.createRange()
    startMatch = matches[0]
#    console.log "StartMatch is: "
#    console.log startMatch
    startNode = startMatch.element.pathInfo.node
    startPath = startMatch.element.pathInfo.path
    startOffset = startMatch.startCorrected
    if startMatch.full
#      console.log "Calling range.setStartBefore <" + startPath + ">..."
#      console.log startNode
      r.setStartBefore startNode
      startInfo = startPath
    else
#      console.log "Calling range.setStart <" + startPath + ">, " + startOffset + "..."
#      console.log startNode
      r.setStart startNode, startOffset
      startInfo = startPath + ":" + startOffset

    endMatch = matches[matches.length - 1]
#    console.log "endMatch is: "
#    console.log endMatch
    endNode = endMatch.element.pathInfo.node
    endPath = endMatch.element.pathInfo.path
    endOffset = endMatch.endCorrected
    if endMatch.full
#      console.log "Calling range.setEndAfter <" + endPath + ">..."
#      console.log endNode
      r.setEndAfter endNode
      endInfo = endPath
    else
#      console.log "Calling range.setEnd <" + endPath + ">, " + endOffset + "..."
#      console.log endNode
      r.setEnd endNode, endOffset
      endInfo = endPath + ":" + endOffset

#    console.log "Has built range: "
#    console.log r

    result = {
      nodes: matches
      range: r
      rangeInfo:
        startPath: startPath
        startOffset: startOffset
        startInfo: startInfo
        endPath: endPath
        endOffset: endOffset
        endInfo: endInfo
      safeParent: r.commonAncestorContainer
    }
#    console.log "Done collecting"
    result

  # ===== Private methods (never call from outside the module) =======

  timestamp: -> new Date().getTime()

  stringStartsWith: (string, prefix) -> prefix is string.substr 0, prefix.length

  parentPath: (path) -> path.substr 0, path.lastIndexOf "/"

  domChangedSince: (timestamp) ->
    if @lastDOMChange? and timestamp? then @lastDOMChange > timestamp else true

  domStableSince: (timestamp) -> not @domChangedSince timestamp

  getProperNodeName: (node) ->
    nodeName = node.nodeName
    switch nodeName
      when "#text" then return "text()"
      when "#comment" then return "comment()"
      when "#cdata-section" then return "cdata-section()"
      else return nodeName

  getPathTo: (node) ->
    xpath = '';
    while node != @rootNode
      pos = 0
      tempitem2 = node
      while tempitem2
        if tempitem2.nodeName is node.nodeName
          pos++
        tempitem2 = tempitem2.previousSibling

      xpath = (@getProperNodeName node) + (if pos>1 then "[" + pos + ']' else "") + '/' + xpath
      node = node.parentNode
    xpath = (if @rootNode.ownerDocument? then './' else '/') + xpath
    xpath = xpath.replace /\/$/, ''
    xpath

  # This method is called recursively, to collect all the paths in a given sub-tree of the DOM.
  collectPathsForNode: (node) ->
    # Step one: get rendered node content, and store path info, if there is valuable content
    cont = @getNodeContent node, false
    if cont.length
      path = @getPathTo node        
      @allPaths[path] =
        path: path
        content: cont
        length: cont.length
        node : node

    # Step two: cover all children.
    # Q: should we check children even if the goven node had no rendered content?
    # I seem to remember that the answer is yes, but I don't remember why.
    if node.hasChildNodes()
      for child in node.childNodes
        @collectPathsForNode child        
    null

  getBody: -> (@rootWin.document.getElementsByTagName "body")[0]

  regions_overlap: (start1, end1, start2, end2) -> start1 < end2 and start2 < end1

  lookUpNode: (path) ->
    doc = @rootNode.ownerDocument ? @rootNode
    results = doc.evaluate path, @rootNode, null, 0, null
    node = results.iterateNext()

  # save the original selection
  saveSelection: ->
    if @oldRanges? then throw new Error "Selection already saved!"
    sel = @rootWin.getSelection()        
#    console.log "Saving selection: " + sel.rangeCount + " ranges."
    @oldRanges = (sel.getRangeAt i) for i in [0 ... sel.rangeCount]
    switch sel.rangeCount
      when 0 then @oldRanges ?= []
      when 1 then @oldRanges = [ @oldRanges ]

  # restore selection
  restoreSelection: ->
#    console.log "Restoring selection: " + @oldRanges.length + " ranges."
    unless @oldRanges? then throw new Error "No selection to restore."
    sel = @rootWin.getSelection()
    sel.removeAllRanges()
    sel.addRange range for range in @oldRanges
    delete @oldRanges

  # Select the given node (for visual identification), and optionally scroll to it
  selectNode: (node, scroll = false) ->  
    sel = @rootWin.getSelection()

    # clear the selection
    sel.removeAllRanges()

    # create our range, and select it
    range = @rootWin.document.createRange()

    # There is some weird, bogus behaviour in Chrome,
    # triggered by whitespaces between the table tag and it's children.
    # See the select-tbody and the select-the-parent-when-selecting problems
    # described here:
    #    https://github.com/hypothesis/h/issues/280
    # And the WebKit bug report here:
    #    https://bugs.webkit.org/show_bug.cgi?id=110595
    # 
    # To work around this, when told to select specific nodes, we have to
    # do various other things. See bellow.

    if USE_THEAD_TBODY_WORKAROUND and node.nodeType is Node.ELEMENT_NODE and
        node.tagName.toLowerCase() in ["thead", "tbody"] and node.hasChildNodes()
      # This is a thead or a tbody, and selection those is problematic,
      # because if the WebKit bug.
      # (Sometimes it selects nothing, sometimes it selects the whole table.)
      # So we select directly the children instead.
      children = node.childNodes
      range.setStartBefore children[0]
      range.setEndAfter children[children.length - 1]
      sel.addRange range
    else
      if USE_TABLE_TEXT_WORKAROUND and node.nodeType is Node.TEXT_NODE and node.parentNode.tagName.toLowerCase() is "table"
        # This is a text element that should not even be here.
        # Selecting it might select the whole table,
        # so we don't select anything

      else
        range.setStartBefore node
        range.setEndAfter node
        sel.addRange range


    if scroll
      sn = node
      while not sn.scrollIntoViewIfNeeded?
        sn = sn.parentNode
      sn.scrollIntoViewIfNeeded()
    sel

  # Read and convert the text of the current selection.
  readSelectionText: (sel) ->
    sel or= @rootWin.getSelection()
    sel.toString().trim().replace(/\n/g, " ").replace /[ ][ ]+/g, " "

  # Read the "text content" of a sub-tree of the DOM by creating a selection from it
  getNodeSelectionText: (node, shouldRestoreSelection = true) ->
    if shouldRestoreSelection then @saveSelection()

    sel = @selectNode node
    text = @readSelectionText sel

    if shouldRestoreSelection then @restoreSelection()
    text


  # Read out the HTML source text of a given element.
  readSourceText: (node) ->
    unless node? then throw new Error "Called readSourceText with non-existend node."

    text = if node.data?  # text nodes
      node.data
    else if node.innerHTML? # element nodes
      node.innerHTML
    else # something else? must look into this
      console.log "Should read source text of node, but neither .data, nor .innerHtml found."
      console.log "Node is: "
      console.log @getPathTo node
      console.log node
      window.wtfnode = node
      throw new Error "Called readSourceText with a node with no data or innerHTML.."

    # Do some normalization.
    text.replace /\n/g, " "        

  # Convert "display" text indices to "source" text indices.
  computeSourcePositions: (match) ->
#    console.log "In computeSourcePosition"
#    console.log match.element.pathInfo.path
#    console.log match.element.pathInfo.node.data

    # the HTML source of the text inside a text element.
    sourceText = @readSourceText match.element.pathInfo.node
#    console.log "sourceText is '" + sourceText + "'"

    # what gets displayed, when the node is processed by the browser.
    displayText = match.element.pathInfo.content
#    console.log "displayText is '" + displayText + "'"

    # The selected range in displayText.
    displayStart = if match.start? then match.start else 0
    displayEnd = if match.end? then match.end else displayText.length
#    console.log "Display range is: " + displayStart + "-" + displayEnd

    sourceIndex = 0
    displayIndex = 0

    until sourceStart? and sourceEnd?
      sc = sourceText[sourceIndex]
      dc = displayText[displayIndex]
      if sc is dc
        if displayIndex is displayStart
          sourceStart = sourceIndex
        displayIndex++        
        if displayIndex is displayEnd
          sourceEnd = sourceIndex + 1

      sourceIndex++
    match.startCorrected = sourceStart
    match.endCorrected = sourceEnd
#    console.log "computeSourcePosition done. Corrected range is: " + match.startCorrected + "-" + match.endCorrected
    null

  # Internal function used to read out the text content of a given node, as render by the browser.
  # The current implementation uses the browser selection API to do so.
  getNodeContent: (node, shouldRestoreSelection = true) -> @getNodeSelectionText node, shouldRestoreSelection

  # Internal function to collect mapping data from a given DOM element.
  # 
  # Input parameters:
  #    node: the node to scan
  #    path: the path to the node (relative to rootNode
  #    parentContent: the content of the node's parent node (as rendered by the browser)
  #           This is used to determine whether the given node is rendered at all.
  #           If not given, it will be assumed that it is rendered
  #    parentIndex: the starting character offset
  #           of content of this node's parent node in the rendered content
  #    index: ths first character offset position in the content of this node's parent node
  #           where the content of this node might start
  #
  # Returns:
  #    the first character offset position in the content of this node's parent node
  #    that is not accounted for by this node
  collectStrings: (node, path, parentContent = null, parentIndex = 0, index = 0) ->
#    console.log "Scanning path " + path    
#    content = @getNodeContent node, false

    pathInfo = @allPaths[path]
    content = pathInfo?.content

    if not content? or content is ""
      # node has no content            
#      console.log "No content, returning"
      return index
        
    startIndex = if parentContent? then (parentContent.indexOf content, index) else index
    if startIndex is -1
       # content of node is not present in parent's content - probably hidden, or something similar
#       console.log "Content of this not is not present in content of parent, at path " + path
       return index


    endIndex = startIndex + content.length
    atomic = not node.hasChildNodes()
    @mappings[path] =
      pathInfo: pathInfo
      start: parentIndex + startIndex
      end: parentIndex + endIndex
      atomic: atomic

    if @declareMappings
      console.log "Found mappings for [" + @mappings[path].start + ":" + @mappings[path].end + "]: " + pathInfo.content

    if not atomic
      children = node.childNodes
      i = 0
      pos = 0
      typeCount = Object()
      while i < children.length
        child = children[i]
        nodeName = @getProperNodeName child
        oldCount = typeCount[nodeName]
        newCount = if oldCount? then oldCount + 1 else 1
        typeCount[nodeName] = newCount
        childPath = path + "/" + nodeName + (if newCount > 1 then "[" + newCount + "]" else "")
        pos=@collectStrings child, childPath, content, parentIndex + startIndex, pos
        i++

    endIndex

