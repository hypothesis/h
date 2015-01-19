# I18N
gettext = null

if Gettext?
  _gettext = new Gettext(domain: "annotator")
  gettext = (msgid) -> _gettext.gettext(msgid)
else
  gettext = (msgid) -> msgid

_t = (msgid) -> gettext(msgid)

unless jQuery?.fn?.jquery
  console.error(_t("Annotator requires jQuery: have you included lib/vendor/jquery.js?"))

unless JSON and JSON.parse and JSON.stringify
  console.error(_t("Annotator requires a JSON implementation: have you included lib/vendor/json2.js?"))

$ = jQuery

Util = {}

# Public: Flatten a nested array structure
#
# Returns an array
Util.flatten = (array) ->
  flatten = (ary) ->
    flat = []

    for el in ary
      flat = flat.concat(if el and $.isArray(el) then flatten(el) else el)

    return flat

  flatten(array)


# Public: decides whether node A is an ancestor of node B.
#
# This function purposefully ignores the native browser function for this,
# because it acts weird in PhantomJS.
# Issue: https://github.com/ariya/phantomjs/issues/11479
Util.contains = (parent, child) ->
  node = child
  while node?
    if node is parent then return true
    node = node.parentNode
  return false

# Public: Finds all text nodes within the elements in the current collection.
#
# Returns a new jQuery collection of text nodes.
Util.getTextNodes = (jq) ->
  getTextNodes = (node) ->
    if node and node.nodeType != Node.TEXT_NODE
      nodes = []

      # If not a comment then traverse children collecting text nodes.
      # We traverse the child nodes manually rather than using the .childNodes
      # property because IE9 does not update the .childNodes property after
      # .splitText() is called on a child text node.
      if node.nodeType != Node.COMMENT_NODE
        # Start at the last child and walk backwards through siblings.
        node = node.lastChild
        while node
          nodes.push getTextNodes(node)
          node = node.previousSibling

      # Finally reverse the array so that nodes are in the correct order.
      return nodes.reverse()
    else
      return node

  jq.map -> Util.flatten(getTextNodes(this))

# Public: determine the last text node inside or before the given node
Util.getLastTextNodeUpTo = (n) ->
  switch n.nodeType
    when Node.TEXT_NODE
      return n # We have found our text node.
    when Node.ELEMENT_NODE
      # This is an element, we need to dig in
      if n.lastChild? # Does it have children at all?
        result = Util.getLastTextNodeUpTo n.lastChild
        if result? then return result
    else
      # Not a text node, and not an element node.
  # Could not find a text node in current node, go backwards
  n = n.previousSibling
  if n?
    Util.getLastTextNodeUpTo n
  else
    null

# Public: determine the first text node in or after the given jQuery node.
Util.getFirstTextNodeNotBefore = (n) ->
  switch n.nodeType
    when Node.TEXT_NODE
      return n # We have found our text node.
    when Node.ELEMENT_NODE
      # This is an element, we need to dig in
      if n.firstChild? # Does it have children at all?
        result = Util.getFirstTextNodeNotBefore n.firstChild
        if result? then return result
    else
      # Not a text or an element node.
  # Could not find a text node in current node, go forward
  n = n.nextSibling
  if n?
    Util.getFirstTextNodeNotBefore n
  else
    null

# Public: read out the text value of a range using the selection API
#
# This method selects the specified range, and asks for the string
# value of the selection. What this returns is very close to what the user
# actually sees.
Util.readRangeViaSelection = (range) ->
  sel = Util.getGlobal().getSelection() # Get the browser selection object
  sel.removeAllRanges()                 # clear the selection
  sel.addRange range.toRange()          # Select the range
  sel.toString()                        # Read out the selection

Util.xpathFromNode = (el, relativeRoot) ->
  try
    result = simpleXPathJQuery.call el, relativeRoot
  catch exception
    console.log "jQuery-based XPath construction failed! Falling back to manual."
    result = simpleXPathPure.call el, relativeRoot
  result

Util.nodeFromXPath = (xp, root) ->
  steps = xp.substring(1).split("/")
  node = root
  for step in steps
    [name, idx] = step.split "["
    idx = if idx? then parseInt (idx?.split "]")[0] else 1
    node = findChild node, name.toLowerCase(), idx

  node

Util.escape = (html) ->
  html
    .replace(/&(?!\w+;)/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')

Util.uuid = (-> counter = 0; -> counter++)()

Util.getGlobal = -> (-> this)()

# Return the maximum z-index of any element in $elements (a jQuery collection).
Util.maxZIndex = ($elements) ->
  all = for el in $elements
          if $(el).css('position') == 'static'
            -1
          else
            # Use parseFloat since we may get scientific notation for large
            # values.
            parseFloat($(el).css('z-index')) or -1
  Math.max.apply(Math, all)

Util.mousePosition = (e, offsetEl) ->
  # If the offset element is not a positioning root use its offset parent
  unless $(offsetEl).css('position') in ['absolute', 'fixed', 'relative']
    offsetEl = $(offsetEl).offsetParent()[0]
  offset = $(offsetEl).offset()
  {
    top:  e.pageY - offset.top,
    left: e.pageX - offset.left
  }

# Checks to see if an event parameter is provided and contains the prevent
# default method. If it does it calls it.
#
# This is useful for methods that can be optionally used as callbacks
# where the existance of the parameter must be checked before calling.
Util.preventEventDefault = (event) ->
  event?.preventDefault?()
