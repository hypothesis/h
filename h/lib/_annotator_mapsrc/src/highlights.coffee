# Abstract highlight class
class Highlight

  constructor: (@annotator, @annotation, @pageIndex) ->

  # Mark/unmark this hl as temporary (while creating an annotation)
  setTemporary: (value) ->
    throw "Operation not implemented."

  # Is this a temporary hl?
  isTemporary: ->
    throw "Operation not implemented."

  # Mark/unmark this hl as active
  setActive: (value) ->
    throw "Operation not implemented."

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
  getBottom: -> getTop() + getBottom()

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


# Simple text highlight
class TextHighlight extends Highlight

  # Is this element a text highlight physical anchor ?
  @isInstance: (element) -> $(element).hasClass 'annotator-hl'

  # Find the first parent outside this physical anchor
  @getIndependentParent: (element) ->
    $(element).parents(':not([class^=annotator-hl])')[0]

  # List of annotators we have already set up events for
  @_inited: []

  # Set up events for this annotator
  @_init: (annotator) ->
    return if annotator in @_inited

    getAnnotations = (event) ->
      annotations = $(event.target)
        .parents('.annotator-hl')
        .andSelf()
        .map -> return $(this).data("annotation")

    annotator.addEvent ".annotator-hl", "mouseover", (event) =>
      annotator.onAnchorMouseover getAnnotations event

    annotator.addEvent ".annotator-hl", "mouseout", (event) =>
      annotator.onAnchorMouseout getAnnotations event

    annotator.addEvent ".annotator-hl", "mousedown", (event) =>
      annotator.onAnchorMousedown getAnnotations event

    annotator.addEvent ".annotator-hl", "click", (event) =>
      annotator.onAnchorClick getAnnotations event

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

    hl = $("<span class='#{cssClass}'></span>")

    # Ignore text nodes that contain only whitespace characters. This prevents
    # spans being injected between elements that can only contain a restricted
    # subset of nodes such as table rows and lists. This does mean that there
    # may be the odd abandoned whitespace node in a paragraph that is skipped
    # but better than breaking table layouts.

    for node in normedRange.textNodes() when not white.test node.nodeValue
      r = $(node).wrapAll(hl).parent().show()[0]
      window.DomTextMapper.changed node, "created hilite"
      r

  # Public: highlight a list of ranges
  #
  # normedRanges - An array of NormalizedRanges to be highlighted.
  # cssClass - A CSS class to use for the highlight (default: 'annotator-hl')
  #
  # Returns an array of highlight Elements.
  _highlightRanges: (normedRanges, cssClass='annotator-hl') ->
    highlights = []
    for r in normedRanges
      $.merge highlights, this._highlightRange(r, cssClass)
    highlights

  constructor: (annotator, annotation, pageIndex, realRange) ->
    TextHighlight._init annotator
    super annotator, annotation, pageIndex
    browserRange = new Range.BrowserRange realRange
    range = browserRange.normalize @annotator.wrapper[0]

    # Create a highlights, and link them with the annotation
    @_highlights = @_highlightRange range

  # Implementing the required APIs
  isTemporary: -> @_temporary

  setTemporary: (value) ->
    @_temporary = value
    if value
      $(@_highlights).addClass('annotator-hl-temporary')
    else
      $(@_highlights).removeClass('annotator-hl-temporary')

  setActive: (value) ->
    if value
      $(@_highlights).addClass('annotator-hl-active')
    else
      $(@_highlights).removeClass('annotator-hl-active')

  _getDOMElements: -> @_highlights

  removeFromDocument: ->
    # remove the highlights added by this anchor
    for hl in @_highlights
      # Is this highlight actually the part of the document?
      if hl.parentNode? and @annotator.domMapper.isPageMapped @pageIndex
        # We should restore original state
        child = hl.childNodes[0]
        $(hl).replaceWith hl.childNodes
        window.DomTextMapper.changed child.parentNode,
          "removed hilite (annotation deleted)"
