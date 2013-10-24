# Annotator plugin for annotating documents handled by PDF.js
class Annotator.Plugin.PDF extends Annotator.Plugin

  pluginInit: ->
    @annotator.documentAccessStrategies.unshift
      # Strategy to handle PDF documents rendered by PDF.js
      name: "PDF.js"
      mapper: PDFTextMapper
