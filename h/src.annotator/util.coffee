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
            parseInt($(el).css('z-index'), 10) or -1
  Math.max.apply(Math, all)

Util.mousePosition = (e, offsetEl) ->
  offset = $(offsetEl).position()
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