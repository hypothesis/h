Annotator = @Annotator
$ = Annotator.$


class Annotator.Guest extends Annotator
  SHOW_HIGHLIGHTS_CLASS = 'annotator-highlights-always-on'

  # Events to be bound on Annotator#element.
  events:
    ".annotator-adder button click":     "onAdderClick"
    ".annotator-adder button mousedown": "onAdderMousedown"
    ".annotator-adder button mouseup":   "onAdderMouseup"
    "setTool": "onSetTool"
    "setVisibleHighlights": "setVisibleHighlights"

  # Plugin configuration
  options:
    TextHighlights: {}
    EnhancedAnchoring: {}
    DomTextMapper: {}
    TextSelection: {}
    TextRange: {}
    TextPosition: {}
    TextQuote: {}
    FuzzyTextAnchors: {}
    FragmentSelector: {}

  # Internal state
  tool: 'comment'
  visibleHighlights: false

  html: jQuery.extend {}, Annotator::html,
    adder: '<div class="annotator-adder"><button class="h-icon-pen"></button></div>'

  constructor: (element, options, config = {}) ->
    options.noScan = true
    super
    delete @options.noScan

    # Are going to be able to use the PDF plugin here?
    if window.PDFTextMapper?.applicable()
      # If we can, let's load the PDF plugin.
      @options.PDF = {}
    else
      # If we can't use the PDF plugin,
      # let's load the Document plugin instead.
      @options.Document = {}

    @frame = $('<div></div>')
    .appendTo(@wrapper)
    .addClass('annotator-frame annotator-outer annotator-collapsed')

    delete @options.app

    bridgePluginOptions =
      discoveryOptions: {}
      bridgeOptions:
        scope: 'annotator:bridge'
      annotationSyncOptions:
        on: (event, handler) =>
          this.subscribe(event, handler)
        emit: (event, args...) =>
          switch event
            # AnnotationSync tries to emit some events without taking actions.
            # We catch them and perform the right action (which will then emit
            # the event for real)
            when 'annotationDeleted'
              this.deleteAnnotation(args...)
            when 'loadAnnotations'
              this.loadAnnotations(args...)
            # Other events can simply be emitted.
            else
              this.publish(event, args)
        formatter: (annotation) =>
          formatted = {}
          formatted.uri = @getHref()
          for k, v of annotation when k isnt 'anchors'
            formatted[k] = v
          # Work around issue in jschannel where a repeated object is considered
          # recursive, even if it is not its own ancestor.
          if formatted.document?.title
            formatted.document.title = formatted.document.title.slice()
          formatted

    this.addPlugin('Bridge', bridgePluginOptions)
    @panel = this._connectAnnotationUISync(this.plugins.Bridge)

    # Load plugins
    for own name, opts of @options
      if not @plugins[name] and Annotator.Plugin[name]
        this.addPlugin(name, opts)

    unless config.dontScan
      # Scan the document text with the DOM Text libraries
      this.anchoring._scan()

    # Watch for newly rendered highlights, and update positions in sidebar
    this.subscribe "highlightsCreated", (highlights) =>
      unless Array.isArray highlights
        highlights = [highlights]
      highlights.forEach (hl) ->
        hls = hl.anchor.highlight  # Fetch all the highlights
        # Get the pages we have highlights on (for the given anchor)
        pages = Object.keys(hls).map (s) -> parseInt s
        firstPage = pages.sort()[0]  # Determine the first page
        firstHl = hls[firstPage]     # Determine the first (topmost) hl
        # Store the position of this anchor inside target
        hl.anchor.target.pos =
          top: hl.getTop()
          height: hl.getHeight()

      # Collect all impacted annotations
      annotations = (hl.annotation for hl in highlights)

      # Announce the new positions, so that the sidebar knows
      this.plugins.Bridge.sync(annotations)

    # Watch for removed highlights, and update positions in sidebar
    this.subscribe "highlightRemoved", (highlight) =>
      hls = highlight.anchor.highlight  # Fetch all the highlights
      # Get the pages we have highlights on (for the given anchor)
      pages = Object.keys(hls).map (s) -> parseInt s
      # Do we have any highlights left?
      if pages.length
        firstPage = pages.sort()[0]  # Determine the first page
        firstHl = hls[firstPage]     # Determine the first (topmost) hl
        # Store the position of this anchor inside target
        highlight.anchor.target.pos =
          top: highlight.getTop()
          heigth: highlight.getHeight()
      else
        delete highlight.anchor.target.pos

      # Announce the new positions, so that the sidebar knows
      this.plugins.Bridge.sync([highlight.annotation])

  # Utility function to remove the hash part from a URL
  _removeHash: (url) ->
    url = new URL url
    url.hash = ""
    url.toString()

  # Utility function to get the decoded form of the document URI
  getRawHref: ->
    if @plugins.PDF
      @plugins.PDF.uri()
    else
      @plugins.Document.uri()

  # Utility function to get a de-hashed form of the document URI
  getHref: -> @_removeHash @getRawHref()

  # Utility function to filter metadata and de-hash the URIs
  getMetadata: =>
    metadata = @plugins.Document?.metadata
    metadata.link?.forEach (link) => link.href = @_removeHash link.href
    metadata

  _connectAnnotationUISync: (bridge) ->
    bridge.onConnect(=> this.publish('panelReady'))
    bridge.on('onEditorHide', this.onEditorHide)
    bridge.on('onEditorSubmit', this.onEditorSubmit)
    bridge.on 'focusAnnotations', (ctx, tags=[]) =>
      for hl in @anchoring.getHighlights()
        if hl.annotation.$$tag in tags
          hl.setFocused true
        else
          hl.setFocused false
    bridge.on 'scrollToAnnotation', (ctx, tag) =>
      for hl in @anchoring.getHighlights()
        if hl.annotation.$$tag is tag
          hl.scrollTo()
          return
    bridge.on 'getDocumentInfo', (trans) =>
      (@plugins.PDF?.getMetaData() ? Promise.reject())
        .then (md) =>
           trans.complete
             uri: @getHref()
             metadata: md
        .catch (problem) =>
           trans.complete
             uri: @getHref()
             metadata: @getMetadata()
        .catch (e) ->

      trans.delayReturn(true)
    bridge.on 'setTool', (ctx, name) =>
      @tool = name
      this.publish 'setTool', name
    bridge.on 'setVisibleHighlights', (ctx, state) =>
      this.publish 'setVisibleHighlights', state

  _setupWrapper: ->
    @wrapper = @element
    .on 'click', (event) =>
      if @selectedTargets?.length
        if @tool is 'highlight'
          # Create the annotation
          annotation = this.setupAnnotation(this.createAnnotation())
      else
        @hideFrame()
    this

  # These methods aren't used in the iframe-hosted configuration of Annotator.
  _setupDynamicStyle: -> this
  _setupViewer: -> this
  _setupEditor: -> this
  _setupDocumentEvents: ->
    $(document).bind({
      # omit the "mouseup" check
      "mousedown": this.checkForStartSelection
    })
    this

  destroy: ->
    $(document).unbind({
      "mouseup":   this.checkForEndSelection
      "mousedown": this.checkForStartSelection
    })

    $('#annotator-dynamic-style').remove()

    @adder.remove()
    @frame.remove()

    @wrapper.find('.annotator-hl').each ->
      $(this).contents().insertBefore(this)
      $(this).remove()

    @element.data('annotator', null)

    for name, plugin of @plugins
      @plugins[name].destroy()

    this.removeEvents()

  createAnnotation: ->
    annotation = super
    this.plugins.Bridge.sync([annotation])
    annotation

  showAnnotations: (annotations) =>
    @panel?.notify
      method: "showAnnotations"
      params: (a.$$tag for a in annotations)

  toggleAnnotationSelection: (annotations) =>
    @panel?.notify
      method: "toggleAnnotationSelection"
      params: (a.$$tag for a in annotations)

  updateAnnotations: (annotations) =>
    @panel?.notify
      method: "updateAnnotations"
      params: (a.$$tag for a in annotations)

  showEditor: (annotation) =>
    @panel?.notify
      method: "showEditor"
      params: annotation.$$tag

  focusAnnotations: (annotations) =>
    @panel?.notify
      method: "focusAnnotations"
      params: (a.$$tag for a in annotations)

  onAnchorMousedown: ->

  checkForStartSelection: (event) =>
    # Override to prevent Annotator choking when this ties to access the
    # viewer but preserve the manipulation of the attribute `mouseIsDown` which
    # is needed for preventing the panel from closing while annotating.
    unless event and this.isAnnotator(event.target)
      @mouseIsDown = true

  # This is called to create a target from a raw selection,
  # using selectors created by the registered selector creators
  _getTargetFromSelection: (selection) ->
    source: @getHref()
    selector: @anchoring.getSelectorsFromSelection(selection)

  confirmSelection: ->
    return true unless @selectedTargets.length is 1

    quote = @getQuoteForTarget @selectedTargets[0]

    if quote.length > 2 then return true

    return confirm "You have selected a very short piece of text: only " + length + " chars. Are you sure you want to highlight this?"

  onSuccessfulSelection: (event, immediate) ->
    if @tool is 'highlight'
      # Do we really want to make this selection?
      return false unless this.confirmSelection()
      # Describe the selection with targets
      @selectedTargets = (@_getTargetFromSelection(s) for s in event.segments)
      return

    unless event?
      throw "Called onSuccessfulSelection without an event!"
    unless event.segments?
      throw "Called onSuccessulSelection with an event with missing segments!"

    # Describe the selection with targets
    @selectedTargets = (@_getTargetFromSelection s for s in event.segments)

    # Do we want immediate annotation?
    if immediate
      # Create an annotation
      @onAdderClick event
    else
      # Show the adder button
      @adder
        .css(Annotator.Util.mousePosition(event, @wrapper[0]))
        .show()

    true

  onFailedSelection: (event) ->
    @adder.hide()
    @selectedTargets = []

  # Select some annotations.
  #
  # toggle: should this toggle membership in an existing selection?
  selectAnnotations: (annotations, toggle) =>
    if toggle
      # Tell sidebar to add these annotations to the sidebar
      this.toggleAnnotationSelection annotations
    else
      # Tell sidebar to show the viewer for these annotations
      this.showAnnotations annotations

  # When hovering on a highlight in highlighting mode,
  # tell the sidebar to hilite the relevant annotations
  onAnchorMouseover: (event) ->
    if @visibleHighlights or @tool is 'highlight'
      event.stopPropagation()
      annotations = event.data.getAnnotations(event)
      this.focusAnnotations annotations

  # When leaving a highlight (with the cursor) in highlighting mode,
  # tell the sidebar to stop hiliting the relevant annotations
  onAnchorMouseout: (event) ->
    if @visibleHighlights or @tool is 'highlight'
      event.stopPropagation()
      this.focusAnnotations []

  # When clicking on a highlight in highlighting mode,
  # tell the sidebar to bring up the viewer for the relevant annotations
  onAnchorClick: (event) =>
    if @visibleHighlights or @tool is 'highlight'
      event.stopPropagation()
      this.selectAnnotations (event.data.getAnnotations event),
        (event.metaKey or event.ctrlKey)

  setTool: (name) ->
    @panel?.notify
      method: 'setTool'
      params: name

  # Pass true to show the highlights in the frame or false to disable.
  setVisibleHighlights: (shouldShowHighlights) ->
    return if @visibleHighlights == shouldShowHighlights

    @panel?.notify
      method: 'setVisibleHighlights'
      params: shouldShowHighlights

    this.toggleHighlightClass(shouldShowHighlights)

  toggleHighlightClass: (shouldShowHighlights) ->
    if shouldShowHighlights
      @element.addClass(SHOW_HIGHLIGHTS_CLASS)
    else
      @element.removeClass(SHOW_HIGHLIGHTS_CLASS)

    @visibleHighlights = shouldShowHighlights

  addComment: ->
    this.showEditor(this.createAnnotation())

  # Open the sidebar
  showFrame: ->
    @panel?.notify method: 'open'

  # Close the sidebar
  hideFrame: ->
    @panel?.notify method: 'back'

  addToken: (token) =>
    @api.notify
      method: 'addToken'
      params: token

  onAdderMouseup: (event) ->
    event.preventDefault()
    event.stopPropagation()

  onAdderMousedown: ->

  onAdderClick: (event) =>
    event.preventDefault()
    event.stopPropagation()
    @adder.hide()
    annotation = this.setupAnnotation(this.createAnnotation())
    Annotator.Util.getGlobal().getSelection().removeAllRanges()
    this.showEditor(annotation)

  onSetTool: (name) ->
    switch name
      when 'comment'
        this.setVisibleHighlights this.visibleHighlights
      when 'highlight'
        this.setVisibleHighlights true
