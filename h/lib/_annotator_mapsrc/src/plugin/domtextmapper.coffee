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
        options.rootNode.addEventListener "corpusChange", @_onCorpusChange
        mapper

  _onCorpusChange: =>
    if @options.trackChanges
      @_trackChanges()
    else
      console.log "WARNING: Corpus has changed. Expect trouble!"

  _trackChanges: ->
    console.log "Engaging experimental document change tracking mode"

    # Phase 1: remove all the anchors

    # We will collect all the annotations, starting from the orphan ones
    annotations = @annotator.orphans.slice()

    for page, anchors of @annotator.anchors  # Go over all the pages
      for anchor in anchors.slice() # And all the anchors
        # Get the annotation
        annotation = anchor.annotation

        # Add this annotation to our collection
        annotations.push annotation unless annotation in annotations

        # Remove this anchor from both the pages and the annotation
        anchor.remove true

    # Phase 2: re-anchor all annotations

    for annotation in annotations # Go over all annotations
      @annotator.anchorAnnotation annotation # and anchor them

    # Phase 3: send out notifications and updates

    @annotator.publish "annotationsLoaded", [annotations.slice()]
