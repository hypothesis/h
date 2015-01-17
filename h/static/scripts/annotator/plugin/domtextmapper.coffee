# Annotator plugin providing dom-text-mapper
class Annotator.Plugin.DomTextMapper extends Annotator.Plugin

  pluginInit: ->
    if @options.skip
      console.log "Not registering DOM-Text-Mapper."
      return

    @anchoring = @annotator.anchoring

    @anchoring.documentAccessStrategies.unshift
      # Document access strategy for simple HTML documents,
      # with enhanced text extraction and mapping features.
      name: "DOM-Text-Mapper"
      mapper: window.DomTextMapper
      init: => @anchoring.document.setRootNode @annotator.wrapper[0]
