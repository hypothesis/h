class window.DomTextMapper

  USE_TABLE_TEXT_WORKAROUND = true
  USE_EMPTY_TEXT_WORKAROUND = true
  SELECT_CHILDREN_INSTEAD = ["thead", "tbody", "ol", "a", "caption", "p"]
  CONTEXT_LEN = 32

  @instances: []

  @changed: (node, reason = "no reason") ->
    if @instances.length is 0 then return
#    dm = @instances[0]
#    console.log "Node @ " + (dm.getPathTo node) + " has changed: " + reason
    for instance in @instances when instance.rootNode.contains(node)
      instance.performUpdateOnNode node
    null

  constructor: ->
    @setRealRoot()
    window.DomTextMapper.instances.push this

  # ===== Public methods =======

  # Consider only the sub-tree beginning with the given node.
  # 
  # This will be the root node to use for all operations.
  setRootNode: (rootNode) ->
    @rootWin = window     
    @pathStartNode = @rootNode = rootNode

  # Consider only the sub-tree beginning with the node whose ID was given.
  # 
  # This will be the root node to use for all operations.
  setRootId: (rootId) -> @setRootNode document.getElementById rootId

  # Use this iframe for operations.
  #
  # Call this when mapping content in an iframe.
  setRootIframe: (iframeId) ->
    iframe = window.document.getElementById iframeId
    unless iframe?
      throw new Error "Can't find iframe with specified ID!"
    @rootWin = iframe.contentWindow
    unless @rootWin?
      throw new Error "Can't access contents of the specified iframe!"
    @rootNode = @rootWin.document
    @pathStartNode = @getBody()

  # Return the default path
  getDefaultPath: -> @getPathTo @pathStartNode

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
  # The usage of this feature is not mandatorry; if not receiving change
  # notifications, the library will just assume that the document can change
  # anythime, and therefore will not assume any stability.
  documentChanged: ->
    @lastDOMChange = @timestamp()
#    console.log "Registered document change."

  # Scan the document
  #
  # Traverses the DOM, collects various information, and
  # creates mappings between the string indices
  # (as appearing in the rendered text) and the DOM elements.  
  # 
  # An map is returned, where the keys are the paths, and the
  # values are objects with info about those parts of the DOM.
  #   path: the valid path value
  #   node: reference to the DOM node
  #   content: the text content of the node, as rendered by the browser
  #   length: the length of the next content
  scan: ->
    if @domStableSince @lastScanned
      # We have a valid paths structure!
#      console.log "We have a valid DOM structure cache."
      return @path

    unless @pathStartNode.ownerDocument.body.contains @pathStartNode
      # We cannot map nodes that are not attached.
      return @path

#    console.log "No valid cache, will have to do a scan."
    startTime = @timestamp()
    @saveSelection()
    @path = {}
    @traverseSubTree @pathStartNode, @getDefaultPath()
    t1 = @timestamp()
#    console.log "Phase I (Path traversal) took " + (t1 - startTime) + " ms."

    path = @getPathTo @pathStartNode
    node = @path[path].node
    @collectPositions node, path, null, 0, 0
    @restoreSelection()
    @lastScanned = @timestamp()
    @corpus = @path[path].content
#    console.log "Corpus is: " + @corpus

    t2 = @timestamp()    
#    console.log "Phase II (offset calculation) took " + (t2 - t1) + " ms."

    @path
 
  # Select the given path (for visual identification),
  # and optionally scroll to it
  selectPath: (path, scroll = false) ->
    info = @path[path]
    unless info? then throw new Error "I have no info about a node at " + path
    node = info?.node
    node or= @lookUpNode info.path
    @selectNode node, scroll
 
  performUpdateOnNode: (node, escalating = false) ->
    unless node? then throw new Error "Called performUpdate with a null node!"
    unless @path? then return #We don't have data yet. Not updating.
    startTime = @timestamp()
    unless escalating then @saveSelection()
    path = @getPathTo node
    pathInfo = @path[path]
    unless pathInfo?
      @performUpdateOnNode node.parentNode, true
      unless escalating then @restoreSelection()        
      return
#    console.log "Performing update on node @ path " + path

#    if escalating then console.log "(Escalated)"
#    console.log "Updating data about " + path + ": "
    if pathInfo.node is node and pathInfo.content is @getNodeContent node, false
#      console.log "Good, the node and the overall content is still the same"
#      console.log "Dropping obsolete path info for children..."
      prefix = path + "/"
      pathsToDrop =p

      # FIXME: There must be a more elegant way to do this. 
      pathsToDrop = []
      for p, data of @path when @stringStartsWith p, prefix
        pathsToDrop.push p
      for p in pathsToDrop
        delete @path[p]        
        
#      console.log "Done. Collecting new path info..."
      @traverseSubTree node, path

#      console.log "Done. Updating mappings..."

      if pathInfo.node is @pathStartNode
        console.log "Ended up rescanning the whole doc."
        @collectPositions node, path, null, 0, 0
      else
        parentPath = @parentPath path
        parentPathInfo = @path[parentPath]
        unless parentPathInfo?
          throw new Error "While performing update on node " + path +
              ", no path info found for parent path: " + parentPath
        oldIndex = if node is node.parentNode.firstChild
          0
        else
          @path[@getPathTo node.previousSibling].end - parentPathInfo.start
        @collectPositions node, path, parentPathInfo.content,
            parentPathInfo.start, oldIndex
        
#      console.log "Data update took " + (@timestamp() - startTime) + " ms."

    else
#      console.log "Hm..node has been replaced, or overall content has changed!"
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
        throw new Error "Can not keep up with the changes,
 since even the node configured as path start node was replaced."
    unless escalating then @restoreSelection()        

  # Return info for a given path in the DOM
  getInfoForPath: (path) ->
    unless @path?
      throw new Error "Can't get info before running a scan() !"
    result = @path[path]
    unless result?
      throw new Error "Found no info for path '" + path + "'!"
    result

  # Return info for a given node in the DOM
  getInfoForNode: (node) ->
    unless node?
      throw new Error "Called getInfoForNode(node) with null node!"
    @getInfoForPath @getPathTo node

  # Get the matching DOM elements for a given set of charRanges
  # (Calles getMappingsForCharRange for each element in the givenl ist)
  getMappingsForCharRanges: (charRanges) ->
#    console.log "charRanges:"
#    console.log charRanges
    (for charRange in charRanges
      mapping = @getMappingsForCharRange charRange.start, charRange.end
    )

  # Return the rendered value of a part of the dom.
  # If path is not given, the default path is used.
  getContentForPath: (path = null) -> 
    path ?= @getDefaultPath()       
    @path[path].content

  # Return the length of the rendered value of a part of the dom.
  # If path is not given, the default path is used.
  getLengthForPath: (path = null) ->
    path ?= @getDefaultPath()
    @path[path].length

  getDocLength: -> @getLengthForPath()

  # Return a given charRange of the rendered value of a part of the dom.
  # If path is not given, the default path is used.
  getContentForCharRange: (start, end, path = null) ->
    text = @getContentForPath(path).substr start, end - start
    text.trim()

  # Get the context that encompasses the given charRange
  # in the rendered text of the document
  getContextForCharRange: (start, end, path = null) ->
    content = @getContentForPath path
    prefixStart = Math.max 0, start - CONTEXT_LEN
    prefixLen = start - prefixStart
    prefix = content.substr prefixStart, prefixLen
    suffix = content.substr end, prefixLen
    [prefix.trim(), suffix.trim()]
        
  # Get the matching DOM elements for a given charRange
  # 
  # If the "path" argument is supplied, scan is called automatically.
  # (Except if the supplied path is the same as the last scanned path.)
  getMappingsForCharRange: (start, end) ->
    unless (start? and end?)
      throw new Error "start and end is required!"
#    console.log "Collecting nodes for [" + start + ":" + end + "]"
    @scan()

    # Collect the matching path infos
#    console.log "Collecting mappings"
    mappings = []
    for p, info of @path when info.atomic and
        @regions_overlap info.start, info.end, start, end
      do (info) =>
#        console.log "Checking " + info.path
#        console.log info
        mapping =
          element: info

        full = start <= info.start and info.end <= end
        if full
          mapping.full = true
          mapping.wanted = info.content
          mapping.yields = info.content
          mapping.startCorrected = 0
          mapping.endCorrected = 0
        else
          if info.node.nodeType is Node.TEXT_NODE        
            if start <= info.start
              mapping.end = end - info.start
              mapping.wanted = info.content.substr 0, mapping.end
            else if info.end <= end
              mapping.start = start - info.start
              mapping.wanted = info.content.substr mapping.start        
            else
              mapping.start = start - info.start
              mapping.end = end - info.start
              mapping.wanted = info.content.substr mapping.start,
                  mapping.end - mapping.start
     
            @computeSourcePositions mapping
            mapping.yields = info.node.data.substr mapping.startCorrected,
                mapping.endCorrected - mapping.startCorrected
          else if (info.node.nodeType is Node.ELEMENT_NODE) and
              (info.node.tagName.toLowerCase() is "img")
            console.log "Can not select a sub-string from the title of an image.
 Selecting all."
            mapping.full = true
            mapping.wanted = info.content
          else
            console.log "Warning: no idea how to handle partial mappings
 for node type " + info.node.nodeType
            if info.node.tagName? then console.log "Tag: " + info.node.tagName
            console.log "Selecting all."
            mapping.full = true
            mapping.wanted = info.content

        mappings.push mapping
#        console.log "Done with " + info.path

    if mappings.length is 0
      throw new Error "No mappings found for [" + start + ":" + end + "]!"

    mappings = mappings.sort (a, b) -> a.element.start - b.element.start
        
    # Create a DOM range object
#    console.log "Building range..."
    r = @rootWin.document.createRange()
    startMapping = mappings[0]
    startNode = startMapping.element.node
    startPath = startMapping.element.path
    startOffset = startMapping.startCorrected
    if startMapping.full
      r.setStartBefore startNode
      startInfo = startPath
    else
      r.setStart startNode, startOffset
      startInfo = startPath + ":" + startOffset

    endMapping = mappings[mappings.length - 1]
    endNode = endMapping.element.node
    endPath = endMapping.element.path
    endOffset = endMapping.endCorrected
    if endMapping.full
      r.setEndAfter endNode
      endInfo = endPath
    else
      r.setEnd endNode, endOffset
      endInfo = endPath + ":" + endOffset

    result = {
      mappings: mappings
      realRange: r
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

  stringStartsWith: (string, prefix) ->
    prefix is string.substr 0, prefix.length

  stringEndsWith: (string, suffix) ->
    suffix is string.substr string.length - suffix.length

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

  getNodePosition: (node) ->
    pos = 0
    tmp = node
    while tmp
      if tmp.nodeName is node.nodeName
        pos++
      tmp = tmp.previousSibling
    pos

  getPathSegment: (node) ->
    name = @getProperNodeName node
    pos = @getNodePosition node
    name + (if pos > 1 then "[#{pos}]" else "")

  getPathTo: (node) ->
    xpath = '';
    while node != @rootNode
      unless node?
        throw new Error "Called getPathTo on a node which was not a descendant of @rootNode. " + @rootNode
      xpath = (@getPathSegment node) + '/' + xpath
      node = node.parentNode
    xpath = (if @rootNode.ownerDocument? then './' else '/') + xpath
    xpath = xpath.replace /\/$/, ''
    xpath

  # This method is called recursively, to traverse a given sub-tree of the DOM.
  traverseSubTree: (node, path, invisible = false, verbose = false) ->
    # Step one: get rendered node content, and store path info,
    # if there is valuable content
    @underTraverse = path
    cont = @getNodeContent node, false
    @path[path] =
      path: path
      content: cont
      length: cont.length
      node : node
    if cont.length
      if verbose then console.log "Collected info about path " + path
      if invisible
        console.log "Something seems to be wrong. I see visible content @ " +
            path + ", while some of the ancestor nodes reported empty contents.
 Probably a new selection API bug...."
        
    else
      if verbose then console.log "Found no content at path " + path
      invisible = true

    # Step two: cover all children.
    # Q: should we check children even if
    # the given node had no rendered content?
    # A: I seem to remember that the answer is yes, but I don't remember why.
    if node.hasChildNodes()
      for child in node.childNodes
        subpath = path + '/' + (@getPathSegment child)
        @traverseSubTree child, subpath, invisible, verbose
    null

  getBody: -> (@rootWin.document.getElementsByTagName "body")[0]

  regions_overlap: (start1, end1, start2, end2) ->
      start1 < end2 and start2 < end1

  lookUpNode: (path) ->
    doc = @rootNode.ownerDocument ? @rootNode
    results = doc.evaluate path, @rootNode, null, 0, null
    node = results.iterateNext()

  # save the original selection
  saveSelection: ->
    if @savedSelection?
      console.log "Selection saved at:"
      console.log @selectionSaved
      throw new Error "Selection already saved!"
    sel = @rootWin.getSelection()        
#    console.log "Saving selection: " + sel.rangeCount + " ranges."
    @savedSelection = (sel.getRangeAt i) for i in [0 ... sel.rangeCount]
    switch sel.rangeCount
      when 0 then @savedSelection ?= []
      when 1 then @savedSelection = [ @savedSelection ]
    try
      throw new Error "Selection was saved here"
    catch exception
      @selectionSaved = exception.stack

  # restore selection
  restoreSelection: ->
#    console.log "Restoring selection: " + @savedSelection.length + " ranges."
    unless @savedSelection? then throw new Error "No selection to restore."
    sel = @rootWin.getSelection()
    sel.removeAllRanges()
    sel.addRange range for range in @savedSelection
    delete @savedSelection

  # Select the given node (for visual identification),
  # and optionally scroll to it
  selectNode: (node, scroll = false) ->
    unless node?
      throw new Error "Called selectNode with null node!"
    sel = @rootWin.getSelection()

    # clear the selection
    sel.removeAllRanges()

    # create our range, and select it
    realRange = @rootWin.document.createRange()

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

    if node.nodeType is Node.ELEMENT_NODE and node.hasChildNodes() and
        node.tagName.toLowerCase() in SELECT_CHILDREN_INSTEAD
      # This is an element where direct selection sometimes fails,
      # because if the WebKit bug.
      # (Sometimes it selects nothing, sometimes it selects something wrong.)
      # So we select directly the children instead.
      children = node.childNodes
      realRange.setStartBefore children[0]
      realRange.setEndAfter children[children.length - 1]
      sel.addRange realRange
    else
      if USE_TABLE_TEXT_WORKAROUND and node.nodeType is Node.TEXT_NODE and
          node.parentNode.tagName.toLowerCase() is "table"
        # This is a text element that should not even be here.
        # Selecting it might select the whole table,
        # so we don't select anything
      else
        # Normal element, should be selected
        try
          realRange.setStartBefore node
          realRange.setEndAfter node
          sel.addRange realRange
        catch exception
          # This might be caused by the fact that FF can't select a
          # TextNode containing only whitespace.
          # If this is the case, then it's OK.
          unless USE_EMPTY_TEXT_WORKAROUND and @isWhitespace node
            # No, this is not the case. Then this is an error.
            console.log "Warning: failed to scan element @ " + @underTraverse
            console.log "Content is: " + node.innerHTML
            console.log "We won't be able to properly anchor to any text inside this element."
#            throw exception
    if scroll
      sn = node
      while sn? and not sn.scrollIntoViewIfNeeded?
        sn = sn.parentNode
      if sn?
        sn.scrollIntoViewIfNeeded()
      else
        console.log "Failed to scroll to element. (Browser does not support scrollIntoViewIfNeeded?)"
    sel

  # Read and convert the text of the current selection.
  readSelectionText: (sel) ->
    sel or= @rootWin.getSelection()
    sel.toString().trim().replace(/\n/g, " ").replace /\s{2,}/g, " "

  # Read the "text content" of a sub-tree of the DOM by
  # creating a selection from it
  getNodeSelectionText: (node, shouldRestoreSelection = true) ->
    if shouldRestoreSelection then @saveSelection()

    sel = @selectNode node
    text = @readSelectionText sel

    if shouldRestoreSelection then @restoreSelection()
    text


  # Convert "display" text indices to "source" text indices.
  computeSourcePositions: (match) ->
#    console.log "In computeSourcePosition"
#    console.log match.element.path
#    console.log match.element.node.data

    # the HTML source of the text inside a text element.
#    console.log "Calculating source position at " + match.element.path
    sourceText = match.element.node.data.replace /\n/g, " "
#    console.log "sourceText is '" + sourceText + "'"

    # what gets displayed, when the node is processed by the browser.
    displayText = match.element.content
#    console.log "displayText is '" + displayText + "'"

    # The selected charRange in displayText.
    displayStart = if match.start? then match.start else 0
    displayEnd = if match.end? then match.end else displayText.length
#    console.log "Display charRange is: " + displayStart + "-" + displayEnd

    if displayEnd is 0
      # Handle empty text nodes  
      match.startCorrected = 0
      match.endCorrected = 0
      return

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
#    console.log "computeSourcePosition done. Corrected charRange is: " +
#      match.startCorrected + "-" + match.endCorrected
    null

  # Internal function used to read out the text content of a given node,
  # as render by the browser.
  # The current implementation uses the browser selection API to do so.
  getNodeContent: (node, shouldRestoreSelection = true) ->
    @getNodeSelectionText node, shouldRestoreSelection

  # Internal function to collect mapping data from a given DOM element.
  # 
  # Input parameters:
  #    node: the node to scan
  #    path: the path to the node (relative to rootNode
  #    parentContent: the content of the node's parent node
  #           (as rendered by the browser)
  #           This is used to determine whether the given node is rendered
  #           at all.
  #           If not given, it will be assumed that it is rendered
  #    parentIndex: the starting character offset
  #           of content of this node's parent node in the rendered content
  #    index: ths first character offset position in the content of this
  #           node's parent node
  #           where the content of this node might start
  #
  # Returns:
  #    the first character offset position in the content of this node's
  #    parent node that is not accounted for by this node
  collectPositions: (node, path, parentContent = null, parentIndex = 0, index = 0) ->
#    console.log "Scanning path " + path    
#    content = @getNodeContent node, false

    pathInfo = @path[path]
    content = pathInfo?.content

    if not content? or content is ""
      # node has no content, not interesting
      pathInfo.start = parentIndex + index
      pathInfo.end = parentIndex + index
      pathInfo.atomic = false
      return index

    startIndex = if parentContent?
      parentContent.indexOf content, index
    else
      index
    if startIndex is -1
       # content of node is not present in parent's content - probably hidden,
       # or something similar
#       console.log "Content of this not is not present in content of parent,
#         at path " + path
       return index


    endIndex = startIndex + content.length
    atomic = not node.hasChildNodes()
    pathInfo.start = parentIndex + startIndex
    pathInfo.end = parentIndex + endIndex
    pathInfo.atomic = atomic

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
        childPath = path + "/" + nodeName + (if newCount > 1
          "[" + newCount + "]"
        else
          ""
        )
        pos = @collectPositions child, childPath, content,
            parentIndex + startIndex, pos
        i++

    endIndex

  WHITESPACE = /^\s*$/

  # Decides whether a given node is a text node that only contains whitespace
  isWhitespace: (node) ->
    result = switch node.nodeType
      when Node.TEXT_NODE
        WHITESPACE.test node.data
      when Node.ELEMENT_NODE
        mightBeEmpty = true
        for child in node.childNodes
          mightBeEmpty = mightBeEmpty and @isWhitespace child
        mightBeEmpty
      else false
    result
