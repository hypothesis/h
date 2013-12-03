class SubTreeCollection

  constructor: ->
    @roots = []

  # Unite a new node with a pre-existing set of nodex.
  #
  # The rules are as follows:
  #  * If the node is identical to, or a successor of any of the
  #    the existing nodes, then it's dropped.
  #  * Otherwise it's added.
  #  * If the node is an ancestor of any of the existing nodes,
  #    the those nodes are dropper.
  add: (node) ->

    # Is this node already contained by any of the existing subtrees?
    for root in @roots
      return if root.contains node

    # If we made it to this point, then it means that this is new.

    newRoots = @roots.slice()

    # Go over the collected roots, and see if some of them should be dropped
    for root in @roots
      if node.contains root # Is this root obsolete now?
        i = newRoots.indexOf this  # Drop this root
        newRoots[i..i] = []

    # Add the new node to the end of the list
    newRoots.push node

    # Replace the old list with the new one
    @roots = newRoots


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
  scan: (reason = "unknown reason") ->
    # Have we ever scanned?
    if @path?
      # Do an incremental update instead
      @_syncState reason
      return

    unless @pathStartNode.ownerDocument.body.contains @pathStartNode
      # We cannot map nodes that are not attached.
#      @log "This is not attached to dom. Exiting."
      return

    @log "Starting scan, because", reason
    # Forget any recorded changes, we are starting with a clean slate.
    @observer.takeSummaries()
    startTime = @timestamp()
    @saveSelection()
    @path = {}
    @traverseSubTree @pathStartNode, @getDefaultPath()
    t1 = @timestamp()
#    @log "Phase I (Path traversal) took " + (t1 - startTime) + " ms."

    path = @getPathTo @pathStartNode
    node = @path[path].node
    @collectPositions node, path, null, 0, 0
    @_corpus = @getNodeContent @path[path].node, false
    @restoreSelection()
#    @log "Corpus is: " + @_corpus

    t2 = @timestamp()    
#    @log "Phase II (offset calculation) took " + (t2 - t1) + " ms."

    @log "Scan took", t2 - startTime, "ms."

    null
 
  # Select the given path (for visual identification),
  # and optionally scroll to it
  selectPath: (path, scroll = false) ->
    @scan "selectPath('" + path + "')"
    info = @path[path]
    unless info? then throw new Error "I have no info about a node at " + path
    node = info?.node
    node or= @lookUpNode info.path
    @selectNode node, scroll

  # Update the mapping information to react to changes in the DOM
  #
  # node is the sub-tree of the changed part.
  _performUpdateOnNode: (node, reason = "(no reason)") ->
    # We really need a node
    unless node
      throw new Error "Called performUpdate with a null node!"

    # No point in runnign this, we don't even have mapping data yet.
    return unless @path

    # Look up the info we have about this node
    path = @getPathTo node
    pathInfo = @path[path]

    # Do we have data about this node?
    while not pathInfo
      # If not, go up one level.
      @log "We don't have any data about the node @", @path, ". Moving up."
      node = node.parentNode
      path = @getPathTo node
      pathInfo = @path[path]

    # Start the clock
    startTime = @timestamp()

    # Save the selection, since we will have to restore it later.
    @saveSelection()

    #@log reason, ": performing update on node @ path", path,
    #  "(", pathInfo.length, "characters)"

    # Save the old and the new content, for later reference
    oldContent = pathInfo.content
    content = @getNodeContent node, false

    # Decide whether we are dealing with a corpus change
    corpusChanged = oldContent isnt content

    # === Phase 1: Drop the invalidated data

    # @log "Dropping obsolete path info for children..."
    prefix = path + "/" # The path to drop

    # Collect the paths to delete (all children of this node)
    pathsToDrop = (p for p, data of @path when @stringStartsWith p, prefix)

    # Has the corpus changed?
    if corpusChanged
      # If yes, drop all data about this node / path
      pathsToDrop.push path

      # Also save the start and end positions from the pathInfo
      oldStart = pathInfo.start
      oldEnd = pathInfo.end

    # Actually drop the selected paths
    delete @path[p] for p in pathsToDrop

    # === Phase 2: if necessary, modify the parts impacted by this change
    # (Parent nodes and later siblings)

    if corpusChanged
      #@log "Hmm... overall node content has changed @", path, "!"

      @_alterAncestorsMappingData node, path, oldStart, oldEnd, content
      @_alterSiblingsMappingData node, oldStart, oldEnd, content

    # Phase 3: re-scan the invalidated part

    #@log "Collecting new path info for", path

    @traverseSubTree node, path

    #@log "Done. Updating mappings..."

    # Is this the root node?
    if node is @pathStartNode
      # Yes, we have rescanned starting with the root node!
      @log "Ended up rescanning the whole doc."
      @collectPositions node, path, null, 0, 0
    else
      # This was not the root path, so we must have a valid parent.
      parentPath = @_parentPath path
      parentPathInfo = @path[parentPath]

      # Now let's find out where we are inside our parent
      oldIndex = if node is node.parentNode.firstChild
        0
      else
        @path[@getPathTo node.previousSibling].end - parentPathInfo.start

      # Recursively calculate all the positions
      @collectPositions node, path, parentPathInfo.content,
          parentPathInfo.start, oldIndex
        
    #@log "Data update took " + (@timestamp() - startTime) + " ms."

    # Restore the selection
    @restoreSelection()

    # Return whether the corpus has changed
    corpusChanged


  # Given the fact the the corpus of a given note has changed,
  # update the mapping info of its ancestors
  _alterAncestorsMappingData: (node, path, oldStart, oldEnd, newContent) ->

    # Calculate how the length has changed
    lengthDelta = newContent.length - (oldEnd - oldStart)

    # Is this the root node?
    if node is @pathStartNode
      @_ignorePos += lengthDelta

      # Update the corpus
      @_corpus = @getNodeContent node, false

      # There are no more ancestors, so return
      return

    parentPath = @_parentPath path
    parentPathInfo = @path[parentPath]

    # Save old start and end
    opStart = parentPathInfo.start
    opEnd = parentPathInfo.end

    # Calculate where the old content used to go in this parent
    pStart = oldStart - opStart
    pEnd = oldEnd - opStart
    #@log "Relative to the parent: [", pStart, "..", pEnd, "]"

    pContent = parentPathInfo.content

    # Calculate the changed content

    # Get the prefix
    prefix = if pStart
      pContent[.. pStart - 1]
    else
      ""

    # Get the suffix
    suffix = pContent[pEnd ..]

    # Replace the changed part in the parent's content
    parentPathInfo.content = newContent = prefix + newContent + suffix

    # Fix up the length and the end position
    parentPathInfo.length += lengthDelta
    parentPathInfo.end += lengthDelta

    # Do the same with the next ancestor
    @_alterAncestorsMappingData parentPathInfo.node, parentPath, opStart, opEnd,
      newContent


  # Given the fact the the corpus of a given note has changed,
  # update the mapping info of all later nodes.
  _alterSiblingsMappingData: (node, oldStart, oldEnd, newContent) ->
    # Calculate the offset, based on the difference in length
    delta = newContent.length - (oldEnd - oldStart)

    # Go over all the elements that are later then the changed node
    for p, info of @path when info.start >= oldEnd
      # Correct their positions
      info.start += delta
      info.end += delta

  # Return info for a given path in the DOM
  getInfoForPath: (path) ->
    @scan "getInfoForPath('" + path + "')"
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
    @scan "getContentForPath('" + path + "')"
    @path[path].content

  # Return the length of the rendered value of a part of the dom.
  # If path is not given, the default path is used.
  getLengthForPath: (path = null) ->
    path ?= @getDefaultPath()
    @cvan "getLengthForPath('" + path + "')"
    @path[path].length

  getDocLength: ->
    @scan "getDocLength()"
    @_corpus.length

  getCorpus: ->
    @scan "getCorpus()"
    @_corpus

  # Get the context that encompasses the given charRange
  # in the rendered text of the document
  getContextForCharRange: (start, end) ->
    @scan "getContextForCharRange(" + start + ", " + end + ")"
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

    @scan "getMappingsForCharRange(" + start + ", " + end + ")"

#    @log "Collecting nodes for [" + start + ":" + end + "]"

    # Collect the matching path infos
    # @log "Collecting mappings"
    mappings = []
    for p, info of @path when info.atomic and
        @_regions_overlap info.start, info.end, start, end
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

  _parentPath: (path) -> path.substr 0, path.lastIndexOf "/"

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

    # Should this node be ignored?
    return if @_isIgnored node

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

  _regions_overlap: (start1, end1, start2, end2) ->
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
#    @log "In computeSourcePosition",
#      match.element.path,
#      match.element.node.data

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
#    @log "computeSourcePosition done. Corrected charRange is: ",
#      match.startCorrected + "-" + match.endCorrected
    null

  # Internal function used to read out the text content of a given node,
  # as render by the browser.
  # The current implementation uses the browser selection API to do so.
  getNodeContent: (node, shouldRestoreSelection = true) ->
    if (node is @pathStartNode) and @expectedContent?
#      @log "Returning fake expectedContent for getNodeContent"
      return @expectedContent
    content = @getNodeSelectionText node, shouldRestoreSelection
    if (node is @pathStartNode) and @_ignorePos?
      return content[ 0 .. @_ignorePos-1 ]

    content

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

    # Should this node be ignored?
    if @_isIgnored node
      pos = parentIndex + index  # Where were we?
      unless @_ignorePos? and @_ignorePos < pos # Have we seen better ?
        @_ignorePos = pos
      return index

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
      @log "Content of this node is not present in content of parent, at path " + path
#      @log "(Content: '" + content + "'.)"
#      console.trace()
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

  # Internal debug method to verify the consistency of mapping info of a node
  _testNodeMapping: (path, info) ->

    # If the info was not passed in, look it up
    info ?= @path[path]

    # Do we have it?
    unless info
      throw new Error "Could not look up node @ '" + path + "'!"

    # Get the range from corpus
    inCorpus = if info.end
      @_corpus[ info.start .. (info.end - 1) ]
    else
      ""

    # Get the actual node content
    realContent = @getNodeContent info.node

    # Compare stored content with the data in corpus
    ok1 = info.content is inCorpus
    unless ok1
      @log "Mismatch on ", path, ": stored content is",
        "'" + info.content + "'",
        ", range in corpus is",
        "'" + inCorpus + "'"

    # Compare stored content with actual content
    ok2 = info.content is realContent
    unless ok2
      @log "Mismatch on ", path, ": stored content is '", info.content,
        "', actual content is '", realContent, "'."

    [ok1, ok2]

  # Internal debug method to verify the consistency of all mapping info
  _testAllMappings: ->
    @log "Verifying map info: was it all properly traversed?"
    for i, p of @path
      unless p.atomic? then @log i, "is missing data."

    @log "Verifying map info: do nodes match?"
    @_testNodeMapping(path, info) for path, info of @path


  # Fake two-phase / pagination support, used for HTML documents
  getPageIndex: -> 0
  getPageCount: -> 1
  getPageRoot: -> @rootNode
  getPageIndexForPos: -> 0
  isPageMapped: -> true

  # Change tracking ===================

  # Get the list of nodes that should be totally ignored
  _getIgnoredParts: ->
   # Do we have to ignore some parts?
    if @options.getIgnoredParts # Yes, some parts should be ignored.
      # Do we already have them, and are we allowed to cache?
      if @_ignoredParts and @options.cacheIgnoredParts # Yes, in cache
        @_ignoredParts
      else # No cache (yet?). Get a new list!
        @_ignoredParts = @options.getIgnoredParts()
    else # Not ignoring anything; facing reality as it is
      []

  # Determines whether a node should be ignored
  _isIgnored: (node) ->
    for container in @_getIgnoredParts()
      return true if container.contains node
    return false

  # Filter a change list
  _filterChanges: (changes) ->

    # If the list of parts to ignore is empty, don't filter
    return changes if @_getIgnoredParts().length is 0

    # OK, start filtering.

    # Go through added elements
    changes.added = changes.added.filter (element) =>
      not @_isIgnored element

    # Go through removed elements
    removed = changes.removed
    changes.removed = removed.filter (element) =>
      parent = element
      while parent in removed
        parent = changes.getOldParentNode parent
      not @_isIgnored parent

    # Go through attributeChanged elements
    attributeChanged = {}
    for attrName, elementList of changes.attributeChanged ? {}
      list = elementList.filter (element) => not @_isIgnored element
      if list.length
        attributeChanged[attrName] = list
    changes.attributeChanged = attributeChanged

    # Go through the characterDataChanged elements
    changes.characterDataChanged = changes.characterDataChanged.filter (element) => not @_isIgnored element

    # Go through the reordered elements
    changes.reordered = changes.reordered.filter (element) =>
      parent = element.parentNode
      not @_isIgnored parent

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
    trees = new SubTreeCollection()

    # Collect the parents of the added nodes
    trees.add n.parentNode for n in changes.added

    # Collect attribute changed nodes
    for k, list of changes.attributeChanged
      trees.add n for n in list

    # Collect character data changed nodes
    trees.add n for n in changes.characterDataChanged

    # Collect the non-removed parents of removed nodes
    for n in changes.removed
      parent = n
      while (parent in changes.removed) or (parent in changes.reparented)
        parent = changes.getOldParentNode parent
      trees.add parent

    # Collect the parents of reordered nodes
    trees.add n.parentNode for n in changes.reordered

    # Collect the parents of reparented nodes
    for n in changes.reparented
      # Get the current parent
      trees.add n.parentNode

      # Get the old parent
      parent = n
      while (parent in changes.removed) or (parent in changes.reparented)
        parent = changes.getOldParentNode parent
      trees.add parent

    return trees.roots


  # React to the pasted list of changes
  _reactToChanges: (reason, changes, data) ->
    if changes
      changes = @_filterChanges changes # Filter the received changes
    unless changes # Did anything remain ?
#      unless reason is "Observer called"
#      @log reason, ", but no (real) changes detected"
      return

    # Actually react to the changes
#    @log reason, changes

    # Collect the changed sub-trees
    changedNodes = @_getInvolvedNodes changes

    corpusChanged = false

    # Go over the changed parts
    for node in changedNodes
      # Perform an incremental update on them
      if @_performUpdateOnNode node, reason, false, data
        # If this change involved a root change, set the flag
        corpusChanged = true

    # If there was a corpus change, announce it
    if corpusChanged then setTimeout =>
      @log "CORPUS HAS CHANGED"
      event = document.createEvent "UIEvents"
      event.initUIEvent "corpusChange", true, false, window, 0
      @rootNode.dispatchEvent event

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
  _onMutation: (summaries) =>
#    @log "DOM mutated!"
    @_reactToChanges "Observer called", summaries[0]


  # Change the root node, and subscribe to the events
  _changeRootNode: (node) ->
    @observer?.disconnect()
    @rootNode = node
    @observer = new MutationSummary
      callback: @_onMutation
      rootNode: node
      queries: [
        all: true
      ]
    node
