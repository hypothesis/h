# Public: Base class for the Editor and Viewer elements. Contains methods that
# are shared between the two.
class Annotator.Widget extends Delegator
  # Classes used to alter the widgets state.
  classes:
    hide: 'annotator-hide'
    invert:
      x: 'annotator-invert-x'
      y: 'annotator-invert-y'

  # Public: Creates a new Widget instance.
  #
  # element - The Element that represents the widget in the DOM.
  # options - An Object literal of options.
  #
  # Examples
  #
  #   element = document.createElement('div')
  #   widget  = new Annotator.Widget(element)
  #
  # Returns a new Widget instance.
  constructor: (element, options) ->
    super
    @classes = $.extend {}, Annotator.Widget.prototype.classes, @classes

  # Public: Unbind the widget's events and remove its element from the DOM.
  #
  # Returns nothing.
  destroy: ->
    this.removeEvents()
    @element.remove()

  checkOrientation: ->
    this.resetOrientation()

    window   = $(Annotator.Util.getGlobal())
    widget   = @element.children(":first")
    offset   = widget.offset()
    viewport = {
      top:   window.scrollTop(),
      right: window.width() + window.scrollLeft()
    }
    current = {
      top:   offset.top
      right: offset.left + widget.width()
    }

    if (current.top - viewport.top) < 0
      this.invertY()

    if (current.right - viewport.right) > 0
      this.invertX()

    this

  # Public: Resets orientation of widget on the X & Y axis.
  #
  # Examples
  #
  #   widget.resetOrientation() # Widget is original way up.
  #
  # Returns itself for chaining.
  resetOrientation: ->
    @element.removeClass(@classes.invert.x).removeClass(@classes.invert.y)
    this

  # Public: Inverts the widget on the X axis.
  #
  # Examples
  #
  #   widget.invertX() # Widget is now right aligned.
  #
  # Returns itself for chaining.
  invertX: ->
    @element.addClass @classes.invert.x
    this

  # Public: Inverts the widget on the Y axis.
  #
  # Examples
  #
  #   widget.invertY() # Widget is now upside down.
  #
  # Returns itself for chaining.
  invertY: ->
    @element.addClass @classes.invert.y
    this

  # Public: Find out whether or not the widget is currently upside down
  #
  # Returns a boolean: true if the widget is upside down
  isInvertedY: ->
    @element.hasClass @classes.invert.y

  # Public: Find out whether or not the widget is currently right aligned
  #
  # Returns a boolean: true if the widget is right aligned
  isInvertedX: ->
    @element.hasClass @classes.invert.x

