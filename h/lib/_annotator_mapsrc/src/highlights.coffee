# Abstract highlight class
class Highlight

  constructor: (@anchor, @pageIndex) ->
    @annotator = @anchor.annotator
    @annotation = @anchor.annotation

  # Mark/unmark this hl as temporary (while creating an annotation)
  setTemporary: (value) ->
    throw "Operation not implemented."

  # Is this a temporary hl?
  isTemporary: ->
    throw "Operation not implemented."

  # Mark/unmark this hl as active
  #
  # Value specifies whether it should be active or not
  #
  # The 'batch' field specifies whether this call is only one of
  # many subsequent calls, which should be executed together.
  #
  # In this case, a "finalizeHighlights" event will be published
  # when all the flags have been set, and the changes should be
  # executed.
  setActive: (value, batch = false) ->
    throw "Operation not implemented."

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

