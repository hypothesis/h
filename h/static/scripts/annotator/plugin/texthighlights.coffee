$ = Annotator.$

# Public: Wraps the DOM Nodes within the provided range with a highlight
# element of the specified class and returns the highlight Elements.
#
# normedRange - A NormalizedRange to be highlighted.
# cssClass - A CSS class to use for the highlight (default: 'annotator-hl')
#
# Returns an array of highlight Elements.
highlightRange = (normedRange, cssClass='annotator-hl') ->
  white = /^\s*$/

  hl = $("<span class='#{cssClass}'></span>")

  # Ignore text nodes that contain only whitespace characters. This prevents
  # spans being injected between elements that can only contain a restricted
  # subset of nodes such as table rows and lists. This does mean that there
  # may be the odd abandoned whitespace node in a paragraph that is skipped
  # but better than breaking table layouts.

  nodes = $(normedRange.textNodes()).filter((i) -> not white.test @nodeValue)
  r = nodes.wrap(hl).parent().show().toArray()
  for node in nodes
    event = document.createEvent "UIEvents"
    event.initUIEvent "domChange", true, false, window, 0
    event.reason = "created hilite"
    node.dispatchEvent event
  r

class TextHighlight

  @highlightRange: highlightRange

  @createFrom: (segment, anchor, page) ->
    return null if segment.type isnt "magic range"

    new TextHighlight anchor, page, segment.data

  # List of annotators we have already set up events for
  @_inited: []

  # Collect the annotations impacted by an event
  @getAnnotations: (event) ->
    $(event.target)
      .parents('.annotator-hl')
      .andSelf()
      .map(-> $(this).data("annotation"))
      .toArray()

  # Set up events for this annotator
  @_init: (annotator) ->
    return if annotator in @_inited

    annotator.element.delegate ".annotator-hl", "mouseover", this,
       (event) -> annotator.onAnchorMouseover event

    annotator.element.delegate ".annotator-hl", "mouseout", this,
       (event) -> annotator.onAnchorMouseout event

    annotator.element.delegate ".annotator-hl", "mousedown", this,
       (event) -> annotator.onAnchorMousedown event

    annotator.element.delegate ".annotator-hl", "click", this,
       (event) -> annotator.onAnchorClick event

    @_inited.push annotator

  constructor: (@anchor, @pageIndex, normedRange) ->
    @annotation = @anchor.annotation
    @anchoring = @anchor.anchoring
    @annotator = @anchoring.annotator

    TextHighlight._init @annotator

    # Create highlights and link them with the annotation
    @_highlights = TextHighlight.highlightRange(normedRange)
    $(@_highlights).data "annotation", @annotation

  # Is this a temporary hl?
  isTemporary: -> @_temporary

  # Mark/unmark this hl as active
  setTemporary: (value) ->
    @_temporary = value
    if value
      $(@_highlights).addClass('annotator-hl-temporary')
    else
      $(@_highlights).removeClass('annotator-hl-temporary')

  # Mark/unmark this hl as focused
  setFocused: (value) ->
    if value
      $(@_highlights).addClass('annotator-hl-focused')
    else
      $(@_highlights).removeClass('annotator-hl-focused')

  # Remove all traces of this hl from the document
  removeFromDocument: ->
    for hl in @_highlights
      # Is this highlight actually the part of the document?
      if hl.parentNode? and @anchoring.document.isPageMapped @pageIndex
        # We should restore original state
        child = hl.childNodes[0]
        $(hl).replaceWith hl.childNodes

        event = document.createEvent "UIEvents"
        event.initUIEvent "domChange", true, false, window, 0
        event.reason = "removed hilite (annotation deleted)"
        child.parentNode.dispatchEvent event

  # Get the Y offset of the highlight.
  getTop: -> $(@_highlights).offset().top

  # Get the height of the highlight.
  getHeight: -> $(@_highlights).outerHeight true

  # Scroll the highlight into view
  scrollIntoView: ->
    new Promise (resolve, reject) =>
      $(@_highlights).scrollintoview complete: ->
        resolve()

class Annotator.Plugin.TextHighlights extends Annotator.Plugin

  # Plugin initialization
  pluginInit: ->
    # Export the text highlight class for other plugins
    Annotator.TextHighlight = TextHighlight
