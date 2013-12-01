# Annotator plugin providing dom-text-mapper
class Annotator.Plugin.DomTextMapper extends Annotator.Plugin

  pluginInit: ->
    @annotator.documentAccessStrategies.unshift
      # Document access strategy for simple HTML documents,
      # with enhanced text extraction and mapping features.
      name: "DOM-Text-Mapper"
      applicable: -> true
      get: =>
        defaultOptions =
          rootNode: @annotator.wrapper[0]
          getIgnoredParts: -> $.makeArray $ [
            "div.annotator-notice",
            "div.annotator-outer",
            "div.annotator-editor",
            "div.annotator-viewer",
            "div.annotator-adder"
          ].join ", "
          cacheIgnoredParts: true
        options = $.extend {}, defaultOptions, @options.options
        mapper = new window.DomTextMapper options
        options.rootNode.addEventListener "corpusChange",
          @annotator._reanchorAnnotations
        mapper

