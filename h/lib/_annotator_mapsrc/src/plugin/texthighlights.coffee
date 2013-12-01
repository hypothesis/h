# This plugin containts the text highlight implementation,
# required for annotating text.

class TextHighlight extends Annotator.Highlight

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

  # Set up events for this annotator
  @_init: (annotator) ->
    return if annotator in @_inited

    getAnnotations = (event) ->
      # Collect the involved annotations
      annotations = TextHighlight.$(event.target)
        .parents('.annotator-hl')
        .andSelf()
        .map -> return TextHighlight.$(this).data("annotation")

      # Make a proper array out of the list
      TextHighlight.$.makeArray annotations

    annotator.addEvent ".annotator-hl", "mouseover", (event) =>
      annotator.onAnchorMouseover getAnnotations event, @highlightType

    annotator.addEvent ".annotator-hl", "mouseout", (event) =>
      annotator.onAnchorMouseout getAnnotations event, @highlightType

    annotator.addEvent ".annotator-hl", "mousedown", (event) =>
      annotator.onAnchorMousedown getAnnotations event, @highlightType

    annotator.addEvent ".annotator-hl", "click", (event) =>
      annotator.onAnchorClick getAnnotations event, @highlightType

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

    for node in normedRange.textNodes() when not white.test node.nodeValue
      @$(node).wrapAll(hl).parent().show()[0]

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

  # Mark/unmark this hl as active
  setActive: (value) ->
    if value
      @$(@_highlights).addClass('annotator-hl-active')
    else
      @$(@_highlights).removeClass('annotator-hl-active')

  # Remove all traces of this hl from the document
  removeFromDocument: ->
    for hl in @_highlights
      # Is this highlight actually the part of the document?
      if hl.parentNode? and @annotator.domMapper.isPageMapped @pageIndex
        # We should restore original state
        child = hl.childNodes[0]
        @$(hl).replaceWith hl.childNodes

  # Get the HTML elements making up the highlight
  _getDOMElements: -> @_highlights

class Annotator.Plugin.TextHighlights extends Annotator.Plugin

  # Plugin initialization
  pluginInit: ->
    # Export the text highlight class for other plugins
    Annotator.TextHighlight = TextHighlight