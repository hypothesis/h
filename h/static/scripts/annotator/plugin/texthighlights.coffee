$ = Annotator.$

# Abstract highlight class
class Highlight

  constructor: (@anchor, @pageIndex) ->
    @annotation = @anchor.annotation
    @anchoring = @anchor.anchoring
    @annotator = @anchoring.annotator

  # Mark/unmark this hl as temporary (while creating an annotation)
  setTemporary: (value) ->
    throw "Operation not implemented."

  # Is this a temporary hl?
  isTemporary: ->
    throw "Operation not implemented."

  # TODO: review the usage of the batch parameters.

  # Mark/unmark this hl as focused
  #
  # Value specifies whether it should be focused or not
  #
  # The 'batch' field specifies whether this call is only one of
  # many subsequent calls, which should be executed together.
  #
  # In this case, a "finalizeHighlights" event will be published
  # when all the flags have been set, and the changes should be
  # executed.
  setFocused: (value, batch = false) ->
    throw "Operation not implemented."

  # React to changes in the underlying annotation
  annotationUpdated: ->
    #console.log "In HL", this, "annotation has been updated."

  # Remove all traces of this hl from the document
  removeFromDocument: ->
    throw "Operation not implemented."

  # Get the HTML elements making up the highlight
  # If you implement this, you get automatic implementation for the functions
  # below. However, if you need a more sophisticated control mechanism,
  # you are free to leave this unimplemented, and manually implement the
  # rest.
  _getDOMElements: ->
    throw "Operation not implemented."

  # Get the Y offset of the highlight. Override for more control
  getTop: -> $(@_getDOMElements()).offset().top

  # Get the height of the highlight. Override for more control
  getHeight: -> $(@_getDOMElements()).outerHeight true

  # Get the bottom Y offset of the highlight. Override for more control.
  getBottom: -> @getTop() + @getBottom()

  # Scroll the highlight into view. Override for more control
  scrollTo: -> $(@_getDOMElements()).scrollintoview()

  # Scroll the highlight into view, with a comfortable margin.
  # up should be true if we need to scroll up; false otherwise
  paddedScrollTo: (direction) ->
    unless direction? then throw "Direction is required"
    dir = if direction is "up" then -1 else +1
    where = $(@_getDOMElements())
    wrapper = @annotator.wrapper
    defaultView = wrapper[0].ownerDocument.defaultView
    pad = defaultView.innerHeight * .2
    where.scrollintoview
      complete: ->
        scrollable = if this.parentNode is this.ownerDocument
          $(this.ownerDocument.body)
        else
          $(this)
        top = scrollable.scrollTop()
        correction = pad * dir
        scrollable.stop().animate {scrollTop: top + correction}, 300

  # Scroll up to the highlight, with a comfortable margin.
  paddedScrollUpTo: -> @paddedScrollTo "up"

  # Scroll down to the highlight, with a comfortable margin.
  paddedScrollDownTo: -> @paddedScrollTo "down"


# This plugin containts the text highlight implementation,
# required for annotating text.
class TextHighlight extends Highlight

  @createFrom: (segment, anchor, page) ->
    return null if segment.type isnt "magic range"

    new TextHighlight anchor, page, segment.data

  # XXX: This is a temporay workaround until the Highlighter extension
  # PR will be merged which will restore separation properly
  @highlightClass = 'annotator-hl'

  # Save the Annotator class reference, while we have access to it.
  # TODO: Is this really the way to go? How do other plugins do it?
  @Annotator = Annotator
  @$ = Annotator.$
  @highlightType = 'TextHighlight'

  # Is this element a text highlight physical anchor ?
  @isInstance: (element) -> @$(element).hasClass 'annotator-hl'

  # Find the first parent outside this physical anchor
  @getIndependentParent: (element) ->
    @$(element).parents(':not([class^=annotator-hl])')[0]

  # List of annotators we have already set up events for
  @_inited: []

  # Collect the annotations impacted by an event
  @getAnnotations: (event) ->
    TextHighlight.$(event.target)
      .parents('.annotator-hl')
      .andSelf()
      .map( -> TextHighlight.$(this).data("annotation"))
      .toArray()

  # Set up events for this annotator
  @_init: (annotator) ->
    return if annotator in @_inited

    annotator.element.delegate ".annotator-hl", "mouseover", this,
       (event) => annotator.onAnchorMouseover event

    annotator.element.delegate ".annotator-hl", "mouseout", this,
       (event) => annotator.onAnchorMouseout event

    annotator.element.delegate ".annotator-hl", "mousedown", this,
       (event) => annotator.onAnchorMousedown event

    annotator.element.delegate ".annotator-hl", "click", this,
       (event) => annotator.onAnchorClick event

    @_inited.push annotator

  # Public: Wraps the DOM Nodes within the provided range with a highlight
  # element of the specified class and returns the highlight Elements.
  #
  # normedRange - A NormalizedRange to be highlighted.
  # cssClass - A CSS class to use for the highlight (default: 'annotator-hl')
  #
  # Returns an array of highlight Elements.
  _highlightRange: (normedRange, cssClass='annotator-hl') ->
    white = /^\s*$/

    hl = @$("<span class='#{cssClass}'></span>")

    # Ignore text nodes that contain only whitespace characters. This prevents
    # spans being injected between elements that can only contain a restricted
    # subset of nodes such as table rows and lists. This does mean that there
    # may be the odd abandoned whitespace node in a paragraph that is skipped
    # but better than breaking table layouts.

    nodes = @$(normedRange.textNodes()).filter((i) -> not white.test @nodeValue)
    r = nodes.wrap(hl).parent().show().toArray()
    for node in nodes
      event = document.createEvent "UIEvents"
      event.initUIEvent "domChange", true, false, window, 0
      event.reason = "created hilite"
      node.dispatchEvent event
    r

  constructor: (anchor, pageIndex, normedRange) ->
    super anchor, pageIndex
    TextHighlight._init @annotator

    @$ = TextHighlight.$
    @Annotator = TextHighlight.Annotator

    # Create a highlights, and link them with the annotation
    @_highlights = @_highlightRange normedRange
    @$(@_highlights).data "annotation", @annotation

  # Implementing the required APIs

  # Is this a temporary hl?
  isTemporary: -> @_temporary

  # Mark/unmark this hl as active
  setTemporary: (value) ->
    @_temporary = value
    if value
      @$(@_highlights).addClass('annotator-hl-temporary')
    else
      @$(@_highlights).removeClass('annotator-hl-temporary')

  # Mark/unmark this hl as focused
  setFocused: (value) ->
    if value
      @$(@_highlights).addClass('annotator-hl-focused')
    else
      @$(@_highlights).removeClass('annotator-hl-focused')

  # Remove all traces of this hl from the document
  removeFromDocument: ->
    for hl in @_highlights
      # Is this highlight actually the part of the document?
      if hl.parentNode? and @anchoring.document.isPageMapped @pageIndex
        # We should restore original state
        child = hl.childNodes[0]
        @$(hl).replaceWith hl.childNodes

        event = document.createEvent "UIEvents"
        event.initUIEvent "domChange", true, false, window, 0
        event.reason = "removed hilite (annotation deleted)"
        child.parentNode.dispatchEvent event

  # Get the HTML elements making up the highlight
  _getDOMElements: -> @_highlights

class Annotator.Plugin.TextHighlights extends Annotator.Plugin

  # Plugin initialization
  pluginInit: ->
    # Export the text highlight class for other plugins
    Annotator.TextHighlight = TextHighlight
