class window.DomTextMapper

  @applicable: -> true

  USE_TABLE_TEXT_WORKAROUND = true
  USE_EMPTY_TEXT_WORKAROUND = true
  SELECT_CHILDREN_INSTEAD = ["thead", "tbody", "ol", "a", "caption", "p", "span", "div", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "li", "form"]
  CONTEXT_LEN = 32

  @instances: 0

  constructor: (@options = {})->
    @id = @options.id ? "d-t-m #" + DomTextMapper.instances
    if @options.rootNode?
      @setRootNode @options.rootNode
    else
      @setRealRoot()
    DomTextMapper.instances += 1

  log: (msg...) ->
    console.log @id, ": ", msg...

  # ===== Public methods =======

  # Consider only the sub-tree beginning with the given node.
  # 
  # This will be the root node to use for all operations.
  setRootNode: (rootNode) ->
    @rootWin = window
    @pathStartNode = @_changeRootNode rootNode

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
    @_changeRootNode @rootWin.document
    @pathStartNode = @getBody()

  # Return the default path
  getDefaultPath: -> @getPathTo @pathStartNode

  # Work with the whole DOM tree
  # 
  # (This is the default; you only need to call this, if you have configured
  # a different root earlier, and now you want to restore the default setting.)
  setRealRoot: ->
    @rootWin = window
    @_changeRootNode document
    @pathStartNode = @getBody() 

  setExpectedContent: (content) ->
    @expectedContent = content

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
    # Have we ever scanned?
    if @path?
      # Do an incremental update instead
      @_syncState "scan()"
      return

    unless @pathStartNode.ownerDocument.body.contains @pathStartNode
      # We cannot map nodes that are not attached.
#      @log "This is not attached to dom. Exiting."
      return

#    @log "No valid cache, will have to do a scan."
    startTime = @timestamp()
    @saveSelection()
    @path = {}
    @traverseSubTree @pathStartNode, @getDefaultPath()
    t1 = @timestamp()
#    @log "Phase I (Path traversal) took " + (t1 - startTime) + " ms."

    path = @getPathTo @pathStartNode
    node = @path[path].node
    @collectPositions node, path, null, 0, 0
    @restoreSelection()
    @_corpus = @path[path].content
#    @log "Corpus is: " + @_corpus

    t2 = @timestamp()    
#    @log "Phase II (offset calculation) took " + (t2 - t1) + " ms."

    null
 
  # Select the given path (for visual identification),
  # and optionally scroll to it
  selectPath: (path, scroll = false) ->
    @_syncState "selectPath('" + path + "')"
    info = @path[path]
    unless info? then throw new Error "I have no info about a node at " + path
    node = info?.node
    node or= @lookUpNode info.path
    @selectNode node, scroll
 
  performUpdateOnNode: (node, reason, escalating = false) ->
    unless node? then throw new Error "Called performUpdate with a null node!"
    unless @path? then return #We don't have data yet. Not updating.
    startTime = @timestamp()
    unless escalating then @saveSelection()
    path = @getPathTo node
    pathInfo = @path[path]
    unless pathInfo?
      @performUpdateOnNode node.parentNode, "Escalated from " + reason, true
      unless escalating then @restoreSelection()        
      return
    @log reason, ": performing update on node @ path", path,
      "(", pathInfo.length, "characters)"

#    if escalating then @log "(Escalated)"
#    @log "Updating data about " + path + ": "
    if pathInfo.node is node and pathInfo.content is @getNodeContent node, false
#      @log "Good, the node and the overall content is still the same"
#      @log "Dropping obsolete path info for children..."
      prefix = path + "/"
      pathsToDrop =p

      # FIXME: There must be a more elegant way to do this. 
      pathsToDrop = []
      for p, data of @path when @stringStartsWith p, prefix
        pathsToDrop.push p
      for p in pathsToDrop
        delete @path[p]        
        
#      @log "Done. Collecting new path info..."
      @traverseSubTree node, path

#      @log "Done. Updating mappings..."

      if pathInfo.node is @pathStartNode
#        @log "Ended up rescanning the whole doc."
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
        
#      @log "Data update took " + (@timestamp() - startTime) + " ms."

    else
#      @log "Hm..node has been replaced, or overall content has changed!"
      if pathInfo.node isnt @pathStartNode
#        @log "I guess I must go up one level."
        parentNode = if node.parentNode?
#         @log "Node has parent, using that."
          node.parentNode
        else
          parentPath = @parentPath path
#          @log "Node has no parent, will look up " + parentPath
          @lookUpNode parentPath
        @performUpdateOnNode parentNode, "escalated from " + reason, true
      else
        throw new Error "Can not keep up with the changes,
 since even the node configured as path start node was replaced."
    unless escalating then @restoreSelection()        

  # Return info for a given path in the DOM
  getInfoForPath: (path) ->
    @_syncState "getInfoForPath('" + path + "')"
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
  # (Calles getMappingsForCharRange for each element in the given ist)
  getMappingsForCharRanges: (charRanges) ->
    (@getMappingsForCharRange charRange.start, charRange.end) for charRange in charRanges

  # Return the rendered value of a part of the dom.
  # If path is not given, the default path is used.
  getContentForPath: (path = null) ->
    path ?= @getDefaultPath()
    @_syncState "getContentForPath('" + path + "')"
    @path[path].content

  # Return the length of the rendered value of a part of the dom.
  # If path is not given, the default path is used.
  getLengthForPath: (path = null) ->
    path ?= @getDefaultPath()
    @_syncState "getLengthForPath('" + path + "')"
    @path[path].length

  getDocLength: ->
    @_syncState "getDocLength()"
    @_corpus.length

  getCorpus: ->
    @_syncState "getCorpus()"
    @_corpus

  # Get the context that encompasses the given charRange
  # in the rendered text of the document
  getContextForCharRange: (start, end) ->
    @_syncState "getContextForCharRange(" + start + ", " + end + ")"
    prefixStart = Math.max 0, start - CONTEXT_LEN
    prefix = @_corpus[prefixStart .. start - 1]
    suffix = @_corpus[end .. end + CONTEXT_LEN - 1]
    [prefix.trim(), suffix.trim()]
        
  # Get the matching DOM elements for a given charRange
  # 
  # If the "path" argument is supplied, scan is called automatically.
  # (Except if the supplied path is the same as the last scanned path.)
  getMappingsForCharRange: (start, end) ->
    unless (start? and end?)
      throw new Error "start and end is required!"

    @_syncState "getMappingsForCharRange(" + start + ", " + end + ")"

#    @log "Collecting nodes for [" + start + ":" + end + "]"
    @scan()

    # Collect the matching path infos
    # @log "Collecting mappings"
    mappings = []
    for p, info of @path when info.atomic and
        @regions_overlap info.start, info.end, start, end
      do (info) =>
#        @log "Checking " + info.path
#        @log info
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
            @log "Can not select a sub-string from the title of an image.
 Selecting all."
            mapping.full = true
            mapping.wanted = info.content
          else
            @log "Warning: no idea how to handle partial mappings
 for node type " + info.node.nodeType
            if info.node.tagName? then @log "Tag: " + info.node.tagName
            @log "Selecting all."
            mapping.full = true
            mapping.wanted = info.content

        mappings.push mapping
#        @log "Done with " + info.path

    if mappings.length is 0
      @log "Collecting nodes for [" + start + ":" + end + "]"
      @log "Should be: '" + @_corpus[ start .. (end-1) ] + "'."
      throw new Error "No mappings found for [" + start + ":" + end + "]!"

    mappings = mappings.sort (a, b) -> a.element.start - b.element.start
        
    # Create a DOM range object
#    @log "Building range..."
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

    # Return the result
    sections: [result]

  # ===== Private methods (never call from outside the module) =======

  timestamp: -> new Date().getTime()

  stringStartsWith: (string, prefix) ->
    string[ 0 .. prefix.length - 1 ] is prefix

  stringEndsWith: (string, suffix) ->
    string[ string.length - suffix.length .. string.length ] is suffix

  parentPath: (path) -> path.substr 0, path.lastIndexOf "/"

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
      if verbose then @log "Collected info about path " + path
      if invisible
        @log "Something seems to be wrong. I see visible content @ " +
            path + ", while some of the ancestor nodes reported empty contents.
 Probably a new selection API bug...."
        @log "Anyway, text is '" + cont + "'."        
    else
      if verbose then @log "Found no content at path " + path
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
      @log "Selection saved at:"
      @log @selectionSaved
      throw new Error "Selection already saved!"
    sel = @rootWin.getSelection()        
#    @log "Saving selection: " + sel.rangeCount + " ranges."
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
#    @log "Restoring selection: " + @savedSelection.length + " ranges."
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
            @log "Warning: failed to scan element @ " + @underTraverse
            @log "Content is: " + node.innerHTML
            @log "We won't be able to properly anchor to any text inside this element."
#            throw exception
    if scroll
      sn = node
      while sn? and not sn.scrollIntoViewIfNeeded?
        sn = sn.parentNode
      if sn?
        sn.scrollIntoViewIfNeeded()
      else
        @log "Failed to scroll to element. (Browser does not support scrollIntoViewIfNeeded?)"
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
#    @log "In computeSourcePosition"
#    @log match.element.path
#    @log match.element.node.data

    # the HTML source of the text inside a text element.
#    @log "Calculating source position at " + match.element.path
    sourceText = match.element.node.data.replace /\n/g, " "
#    @log "sourceText is '" + sourceText + "'"

    # what gets displayed, when the node is processed by the browser.
    displayText = match.element.content
#    @log "displayText is '" + displayText + "'"

    # The selected charRange in displayText.
    displayStart = if match.start? then match.start else 0
    displayEnd = if match.end? then match.end else displayText.length
#    @log "Display charRange is: " + displayStart + "-" + displayEnd

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
#    @log "computeSourcePosition done. Corrected charRange is: " +
#      match.startCorrected + "-" + match.endCorrected
    null

  # Internal function used to read out the text content of a given node,
  # as render by the browser.
  # The current implementation uses the browser selection API to do so.
  getNodeContent: (node, shouldRestoreSelection = true) ->
    if node is @pathStartNode and @expectedContent?
#      @log "Returning fake expectedContent for getNodeContent"
      @expectedContent
    else
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
#    @log "Scanning path " + path
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
      @log "Content of this not is not present in content of parent, at path " + path
      @log "(Content: '" + content + "'.)"
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

  # Internal debug method to verify the consistency of mapping info
  _testMap: ->
    @log "Verifying map info: was it all properly traversed?"
    for i,p of @path
      unless p.atomic? then @log i + " is missing data."

    @log "Verifying map info: do atomic elements match?"
    for i,p of @path when p.atomic
      expected = @_corpus[p.start .. (p.end - 1) ]
      ok = p.content is expected
      unless ok then @log "Mismatch on " + i + ": content is '" + p.content + "', range in corpus is '" + expected + "'."
      ok

    null

  # Fake two-phase / pagination support, used for HTML documents
  getPageIndex: -> 0
  getPageCount: -> 1
  getPageIndexForPos: -> 0
  isPageMapped: -> true

  # Change tracking ===================

  # Filter a change list
  _filterChanges: (changes) ->
    # If no ignore parts options is set, don't filter        
    return changes unless @options.getIgnoredParts

    # Do we have to re-fetch the list of parts to ignore?
    unless @ignoredParts and @options.cacheIgnoredParts
      @ignoredParts = @options.getIgnoredParts()

    # If the list of parts to ignore is empty, don't filter
    return changes unless @ignoredParts.length

    # OK, start filtering.

    # Go through added elements
    changes.added = changes.added.filter (element) =>
      for container in @ignoredParts
        return false if container.contains element
      return true

    # Go through removed elements
    removed = changes.removed
    changes.removed = removed.filter (element) =>
      parent = element
      while parent in removed
        parent = changes.getOldParentNode parent
      for container in @ignoredParts
        return false if container.contains parent
      return true

    # Go through attributeChanged elements
    attributeChanged = {}
    for attrName, elementList of changes.attributeChanged ? {}
      list = elementList.filter (element) =>
        for container in @ignoredParts
          return false if container.contains element
        return true
      if list.length
        attributeChanged[attrName] = list
    changes.attributeChanged = attributeChanged

    # Go through the characterDataChanged elements
    changes.characterDataChanged = changes.characterDataChanged.filter (element) =>
      for container in @ignoredParts
        return false if container.contains element
      return true

    # Go through the reordered elements
    changes.reordered = changes.reordered.filter (element) =>
      parent = element.parentNode
      for container in @ignoredParts
        return false if container.contains parent
      return true

    # Go through the reparented elements
    # TODO

    attributeChangedCount = 0
    for k, v of changes.attributeChanged
      attributeChangedCount++
    if changes.added.length or
        changes.characterDataChanged.length or
        changes.removed.length or
        changes.reordered.length or
        changes.reparented.length or
        attributeChangedCount
      return changes
    else
      return null

    changes


  # Callect all nodes involved in any of the passed changes
  _getInvolvedNodes: (changes) ->
    nodes = []

    # Collect changed nodes
    for n in changes.added
      nodes.push n unless n in nodes

    # Collect attribute changed nodes
    for k, list of changes.attributeChanged
      for n in list
        oldValue = changes.getOldAttribute n, k
        newValue = n.getAttribute k
#        console.log "Attribute change: ", n.tagName, ".", k, ":",
#          "'" + oldValue + "'",
#          "->",
#          "'" +  newValue + "'"
        nodes.push n unless n in nodes

    # Collect character data changed nodes
    for n in changes.characterDataChanged
      nodes.push n unless n in nodes

    # Collect the non-removed parents of removed nodes
    for n in changes.removed
      parent = n
      while (parent in changes.removed) or (parent in changes.reparented)
        parent = changes.getOldParentNode parent
      nodes.push parent unless parent in nodes

    # Collect the parents of reordered nodes
    for n in changes.reordered
      parent = n.parent
      nodes.push parent unless parent in nodes

    # Collect the parents of reparented nodes
    for n in changes.reparented
      # Get the current parent
      parent = n.parentNode
      nodes.push parent unless parent in nodes

      # Get the old parent
      parent = n
      while (parent in changes.removed) or (parent in changes.reparented)
        parent = changes.getOldParentNode parent
      nodes.push parent unless parent in nodes

    return nodes


  # Determine the first common ancestor of the passed nodes
  _getCommonAncestor: (nodes) ->
    unless nodes?.length
      throw "We need a list of nodes."

    root = nodes[0]             # Start with the first node
    for n in nodes              # Go over all the nodes
      while not root.contains n # Push root up, until it encompasses
        root = root.parentNode  # all
    root


  # React to the pasted list of changes
  _reactToChanges: (reason, changes, data) ->
    if changes
      changes = @_filterChanges changes # Filter the received changes
    unless changes # Did anything remain ?
#      unless reason is "Observer called"
#        @log reason, ", but no (real) changes detected"
      return

    # Actually react to the changes
#    @log reason #, changes

    # Collect all the interesting nodes
    changedNodes = @_getInvolvedNodes changes

    # Get the common root of all changed nodes
    changeRoot = @_getCommonAncestor changedNodes

    # Rescan the involved part
    @performUpdateOnNode changeRoot, reason, false, data

  # Bring the our data up to date
  _syncState: (reason = "i am in the mood", data) ->

    # Get the changes from the observer
    summaries = @observer.takeSummaries()

#    if summaries # react to them
    @_reactToChanges "SyncState for " + reason, summaries?[0], data

  # Change handler, called when we receive a change notification
  _onChange: (event) =>
    @_syncState "change event '" + event.reason + "'", event.data


  # Callback for the mutation observer
  _onMutation: (summaries) => @_reactToChanges "Observer called", summaries[0]


  # Change the root node, and subscribe to the events
  _changeRootNode: (node) ->
    @observer?.disconnect()
    @rootNode?.removeEventListener "domChange", @_onChange
    @rootNode = node
    @rootNode.addEventListener "domChange", @_onChange
    @observer = new MutationSummary
      callback: @_onMutation
      rootNode: node
      queries: [
        all: true
      ]
    node
