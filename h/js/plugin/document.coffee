class Annotator.Plugin.Document extends Annotator.Plugin

  events:
    'beforeAnnotationCreated': 'beforeAnnotationCreated'

  pluginInit: ->
    @metadata = null

  beforeAnnotationCreated: (annotation) =>
    if not @metadata
      @metadata = this.getDocumentMetadata()
    annotation.document = @metadata

  getDocumentMetadata: =>
    $ = jQuery
    @metadata =
      title: $("head title").text()
    return @metadata
