class window.DomTextMatcher extends DTM_MatcherCore
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

  # Scan the document
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

  constructor: (domTextMapper) ->
    super
