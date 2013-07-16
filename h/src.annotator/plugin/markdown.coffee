# Plugin that renders annotation comments displayed in the Viewer in Markdown.
# Requires Showdown library to be present in the page when initialised.
class Annotator.Plugin.Markdown extends Annotator.Plugin
  # Events to be bound to the @element.
  events:
    'annotationViewerTextField': 'updateTextField'

  # Public: Initailises an instance of the Markdown plugin.
  #
  # element - The Annotator#element.
  # options - An options Object (there are currently no options).
  #
  # Examples
  #
  #   plugin = new Annotator.Plugin.Markdown(annotator.element)
  #
  # Returns a new instance of Annotator.Plugin.Markdown.
  constructor: (element, options) ->
    if Showdown?.converter?
      super
      @converter = new Showdown.converter()
    else
      console.error Annotator._t("To use the Markdown plugin, you must include Showdown into the page first.")

  # Annotator event callback. Displays the annotation.text as a Markdown
  # rendered version.
  #
  # field      - The viewer field Element.
  # annotation - The annotation Object being displayed.
  #
  # Examples
  #
  #   # Normally called by Annotator#viewer()
  #   plugin.updateTextField(field, {text: 'My _markdown_ comment'})
  #   $(field).html() # => Returns "My <em>markdown</em> comment"
  #
  # Returns nothing
  updateTextField: (field, annotation) =>
    # Escape any HTML in the text to prevent XSS.
    text = Annotator.Util.escape(annotation.text || '')
    $(field).html(this.convert(text))

  # Converts provided text into markdown.
  #
  # text - A String of Markdown to render as HTML.
  #
  # Examples
  #
  # plugin.convert('This is _very_ basic [Markdown](http://daringfireball.com)')
  # # => Returns "This is <em>very<em> basic <a href="http://...">Markdown</a>"
  #
  # Returns HTML string.
  convert: (text) ->
    @converter.makeHtml text
