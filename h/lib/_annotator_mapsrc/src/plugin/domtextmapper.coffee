# Annotator plugin providing dom-text-mapper
class Annotator.Plugin.DomTextMapper extends Annotator.Plugin

  pluginInit: ->
    @annotator.documentAccessStrategies.unshift
      # Document access strategy for simple HTML documents,
      # with enhanced text extraction and mapping features.
      name: "DOM-Text-Mapper"
      applicable: -> true
      get: => new window.DomTextMapper
        getIgnoredParts: @options.getIgnoredParts
        cacheIgnoredParts: @options.cacheIgnoredParts
        rootNode: @annotator.wrapper[0]
