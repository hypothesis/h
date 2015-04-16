Annotator = require('annotator')

# Save references to Range and Util (because we call Annotator.noConflict() when
# bootstrapping)
Range = Annotator.Range
Util = Annotator.Util

# Disable Annotator's default highlight events
delete Annotator.prototype.events[".annotator-hl mouseover"]
delete Annotator.prototype.events[".annotator-hl mouseout"]

# Override setupAnnotation
Annotator.prototype.setupAnnotation = (annotation) ->
  # If this is a new annotation, we might have to add the targets
  annotation.target ?= @selectedTargets
  @selectedTargets = []

  annotation.anchors = []

  for t in annotation.target ? []
    try
      # Create an anchor for this target
      result = this.anchoring.createAnchor annotation, t
      anchor = result.result
      if result.error? instanceof Range.RangeError
        this.publish 'rangeNormalizeFail', [annotation, result.error.range, result.error]
      if anchor?
        t.diffHTML = anchor.diffHTML
        t.diffCaseOnly = anchor.diffCaseOnly

    catch exception
      console.log "Error in setupAnnotation for", annotation.id,
        ":", exception.stack ? exception

  if annotation.target?.length and not annotation.anchors?.length
    annotation.$orphan = true

  annotation

# Override deleteAnnotation to deal with anchors, not highlights.
Annotator.prototype.deleteAnnotation = (annotation) ->
  if annotation.anchors?
    for a in annotation.anchors
      a.remove()

  this.publish('annotationDeleted', [annotation])
  annotation


# Checks for the presence of wicked-good-xpath
# It is always safe to install it, it'll not overwrite existing functions
g = Annotator.Util.getGlobal()
if g.wgxpath? then g.wgxpath.install()

Range.BrowserRange.prototype.normalize = (root) ->
  if @tainted
    console.error(_t("You may only call normalize() once on a BrowserRange!"))
    return false
  else
    @tainted = true

  r = {}

  # Look at the start
  if @startContainer.nodeType is Node.ELEMENT_NODE
    # We are dealing with element nodes
    r.start = Util.getFirstTextNodeNotBefore @startContainer.childNodes[@startOffset]
    r.startOffset = 0
  else
    # We are dealing with simple text nodes
    r.start = @startContainer
    r.startOffset = @startOffset

  # Look at the end
  if @endContainer.nodeType is Node.ELEMENT_NODE
    # Get specified node.
    node = @endContainer.childNodes[@endOffset]

    if node? # Does that node exist?
      # Look for a text node either at the immediate beginning of node
      n = node
      while n? and (n.nodeType isnt Node.TEXT_NODE)
        n = n.firstChild
      if n? # Did we find a text node at the start of this element?
        # Check the previous sibling
        prev = n.previousSibling
        if prev? and (prev.nodeType is Node.TEXT_NODE)
          # We have another text righ before us. Use that instead.
          r.end = prev
          r.endOffset = prev.nodeValue.length
        else
          # No, we need to stick to this node.
          r.end = n
          r.endOffset = 0

    unless r.end?
      # We need to find a text node in the previous sibling of the node at the
      # given offset, if one exists, or in the previous sibling of its container.
      if @endOffset
        node = @endContainer.childNodes[@endOffset - 1]
      else
        node = @endContainer.previousSibling
      r.end = Util.getLastTextNodeUpTo node
      r.endOffset = r.end.nodeValue.length

  else # We are dealing with simple text nodes
    r.end = @endContainer
    r.endOffset = @endOffset

  # We have collected the initial data.

  # Now let's start to slice & dice the text elements!
  nr = {}
  changed = false

  if r.startOffset > 0
    # Do we really have to cut?
    if r.start.nodeValue.length > r.startOffset
      # Yes. Cut.
      nr.start = r.start.splitText(r.startOffset)
      changed = true
    else
      # Avoid splitting off zero-length pieces.
      nr.start = r.start.nextSibling
  else
    nr.start = r.start

  # is the whole selection inside one text element ?
  if r.start is r.end
    if nr.start.nodeValue.length > (r.endOffset - r.startOffset)
      nr.start.splitText(r.endOffset - r.startOffset)
      changed = true
    nr.end = nr.start
  else # no, the end of the selection is in a separate text element
    # does the end need to be cut?
    if r.end.nodeValue.length > r.endOffset
      r.end.splitText(r.endOffset)
      changed = true
    nr.end = r.end

  # Make sure the common ancestor is an element node.
  nr.commonAncestor = @commonAncestorContainer
  while nr.commonAncestor.nodeType isnt Node.ELEMENT_NODE
    nr.commonAncestor = nr.commonAncestor.parentNode

  if changed
    event = document.createEvent "UIEvents"
    event.initUIEvent "domChange", true, false, window, 0
    event.reason = "range normalization"
    event.data = nr
    nr.commonAncestor.dispatchEvent event

  new Range.NormalizedRange(nr)
