Annotator = @Annotator
$ = Annotator.$


class Annotator.Guest extends Annotator
  # Events to be bound on Annotator#element.
  events:
    ".annotator-adder button click":     "onAdderClick"
    ".annotator-adder button mousedown": "onAdderMousedown"
    "setTool": "onSetTool"
    "setVisibleHighlights": "onSetVisibleHighlights"

  # Plugin configuration
  options:
    TextHighlights: {}
    DomTextMapper: {}
    TextAnchors: {}
    TextRange: {}
    TextPosition: {}
    TextQuote: {}
    FuzzyTextAnchors: {}
    PDF: {}
    Document: {}

  # Internal state
  tool: 'comment'
  visibleHighlights: false

  constructor: (element, options, config = {}) ->
    options.noScan = true
    super
    delete @options.noScan

    @frame = $('<div></div>')
    .appendTo(@wrapper)
    .addClass('annotator-frame annotator-outer annotator-collapsed')

    delete @options.app

    this.addPlugin 'Bridge',
      formatter: (annotation) =>
        formatted = {}
        if annotation.document?
          formatted['uri'] = @plugins.Document.uri()
        for k, v of annotation when k isnt 'anchors'
          formatted[k] = v
        # Work around issue in jschannel where a repeated object is considered
        # recursive, even if it is not its own ancestor.
        if formatted.document?.title
          formatted.document.title = formatted.document.title.slice()
        formatted
      onConnect: (source, origin, scope) =>
        @panel = this._setupXDM
          window: source
          origin: origin
          scope: "#{scope}:provider"
          onReady: =>
            console.log "Guest functions are ready for #{origin}"
            setTimeout =>
              event = document.createEvent "UIEvents"
              event.initUIEvent "annotatorReady", false, false, window, 0
              event.annotator = this
              window.dispatchEvent event

    # Load plugins
    for own name, opts of @options
      if not @plugins[name]
        this.addPlugin(name, opts)

    unless config.dontScan
      # Scan the document text with the DOM Text libraries
      this.scanDocument "Guest initialized"

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
        console.log "We still have something left"
        firstPage = pages.sort()[0]  # Determine the first page
        firstHl = hls[firstPage]     # Determine the first (topmost) hl
        # Store the position of this anchor inside target
        highlight.anchor.target.pos =
          top: highlight.getTop()
          heigth: highlight.getHeight()
      else
        console.log "No pos left"
        delete highlight.anchor.target.pos

      # Announce the new positions, so that the sidebar knows
      this.plugins.Bridge.sync([highlight.annotation])

  _setupXDM: (options) ->
    # jschannel chokes FF and Chrome extension origins.
    if (options.origin.match /^chrome-extension:\/\//) or
        (options.origin.match /^resource:\/\//)
      options.origin = '*'

    channel = Channel.build options

    channel

    .bind('onEditorHide', this.onEditorHide)
    .bind('onEditorSubmit', this.onEditorSubmit)

    .bind('setDynamicBucketMode', (ctx, value) =>
      return unless @plugins.Heatmap
      return if @plugins.Heatmap.dynamicBucket is value
      @plugins.Heatmap.dynamicBucket = value
      if value then @plugins.Heatmap._update()
    )

    .bind('setActiveHighlights', (ctx, tags=[]) =>
      for hl in @getHighlights()
        if hl.annotation.$$tag in tags
          hl.setActive true, true
        else
          unless hl.isTemporary()
            hl.setActive false, true
      this.publish "finalizeHighlights"
    )

    .bind('setFocusedHighlights', (ctx, tags=[]) =>
      for hl in @getHighlights()
        annotation = hl.annotation
        if annotation.$$tag in tags
          hl.setFocused true, true
        else
          hl.setFocused false, true
      this.publish "finalizeHighlights"
    )

    .bind('scrollTo', (ctx, tag) =>
      for hl in @getHighlights()
        if hl.annotation.$$tag is tag
          hl.scrollTo()
          return
    )

    .bind('getDocumentInfo', =>
      return {
        uri: @plugins.Document.uri()
        metadata: @plugins.Document.metadata
      }
    )

    .bind('setTool', (ctx, name) =>
      @tool = name
      this.publish 'setTool', name
    )

    .bind('setVisibleHighlights', (ctx, state) =>
      this.setVisibleHighlights state, false
      this.publish 'setVisibleHighlights', state
    )

    .bind('updateHeatmap', =>
      @plugins.Heatmap._scheduleUpdate()
    )

  scanDocument: (reason = "something happened") =>
    try
      console.log "Analyzing host frame, because " + reason + "..."
      this._scan()
    catch e
      console.log e.message
      console.log e.stack

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
  _setupViewer: -> this
  _setupEditor: -> this

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

  showViewer: (annotations) =>
    @panel?.notify
      method: "showViewer"
      params: (a.$$tag for a in annotations)

  toggleViewerSelection: (annotations) =>
    @panel?.notify
      method: "toggleViewerSelection"
      params: (a.$$tag for a in annotations)

  updateViewer: (annotations) =>
    @panel?.notify
      method: "updateViewer"
      params: (a.$$tag for a in annotations)

  showEditor: (annotation) =>
    @panel?.notify
      method: "showEditor"
      params: annotation.$$tag

  onAnchorMouseover: ->
  onAnchorMouseout: ->
  onAnchorMousedown: ->

  checkForStartSelection: (event) =>
    # Override to prevent Annotator choking when this ties to access the
    # viewer but preserve the manipulation of the attribute `mouseIsDown` which
    # is needed for preventing the panel from closing while annotating.
    unless event and this.isAnnotator(event.target)
      @mouseIsDown = true

  confirmSelection: ->
    return true unless @selectedTargets.length is 1

    quote = @getQuoteForTarget @selectedTargets[0]

    if quote.length > 2 then return true

    return confirm "You have selected a very short piece of text: only " + length + " chars. Are you sure you want to highlight this?"

  onSuccessfulSelection: (event, immediate) ->
    return unless @canAnnotate
    if @tool is 'highlight'
      # Do we really want to make this selection?
      return false unless this.confirmSelection()
      # Describe the selection with targets
      @selectedTargets = (@_getTargetFromSelection(s) for s in event.segments)
      return
    super

  # Select some annotations.
  #
  # toggle: should this toggle membership in an existing selection?
  selectAnnotations: (annotations, toggle) =>
    # Switch off dynamic mode; we are going to "Selection" scope
    @plugins.Heatmap.dynamicBucket = false

    if toggle
      # Tell sidebar to add these annotations to the sidebar
      this.toggleViewerSelection annotations
    else
      # Tell sidebar to show the viewer for these annotations
      this.showViewer annotations

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

  setVisibleHighlights: (state=true, notify=true) ->
    if notify
      @panel?.notify
        method: 'setVisibleHighlights'
        params: state
    else
      markerClass = 'annotator-highlights-always-on'
      if state or this.tool is 'highlight'
        @element.addClass markerClass
      else
        @element.removeClass markerClass

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

  onAdderMousedown: ->

  onAdderClick: (event) =>
    event.preventDefault()
    event.stopPropagation()
    @adder.hide()
    annotation = this.setupAnnotation(this.createAnnotation())
    this.showEditor(annotation)

  onSetTool: (name) ->
    switch name
      when 'comment'
        this.setVisibleHighlights this.visibleHighlights, false
      when 'highlight'
        this.setVisibleHighlights true, false

  onSetVisibleHighlights: (state) =>
    this.visibleHighlights = state
    this.setVisibleHighlights state, false
