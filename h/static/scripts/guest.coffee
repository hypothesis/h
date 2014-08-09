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
  comments: null
  tool: 'comment'
  visibleHighlights: false
  noBack: false

  constructor: (element, options, config = {}) ->
    options.noScan = true
    super
    delete @options.noScan

    # Create an array for holding the comments
    @comments = []

    # These are in focus (visually marked here, and open in sidebar)
    @focusedAnnotations = []

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
        this.publish "enableAnnotating", @canAnnotate
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

    # Watch for deleted comments
    this.subscribe 'annotationDeleted', (annotation) =>
      if this.isComment annotation
        i = @comments.indexOf annotation
        if i isnt -1
          @comments[i..i] = []
          @plugins.Heatmap._update()

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
          heigth: hl.getHeight()

      # Collect all impacted annotations
      annotations = (hl.annotation for hl in highlights)
      # Announce the new positions, so that the sidebar knows
      this.publish "annotationsLoaded", [annotations]

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
      this.publish "annotationsLoaded", [[highlight.annotation]]

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
      this.focusedAnnotations = []
      for hl in @getHighlights()
        annotation = hl.annotation
        if annotation.$$tag in tags
          this.focusedAnnotations.push annotation
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

    .bind('adderClick', =>
      @selectedTargets = @forcedLoginTargets
      @onAdderClick @forcedLoginEvent
      delete @forcedLoginTargets
      delete @forcedLoginEvent
    )

    .bind('getDocumentInfo', =>
      return {
        uri: @plugins.Document.uri()
        metadata: @plugins.Document.metadata
      }
    )

    .bind('showAll', =>
      # Switch off dynamic mode on the heatmap
      if @plugins.Heatmap
        @plugins.Heatmap.dynamicBucket = false

      # Collect all successfully attached annotations
      annotations = []
      for page, anchors of @anchors
        for anchor in anchors
          unless anchor.annotation in annotations
            annotations.push anchor.annotation

      # Show all the annotations
      @updateViewer "Document", annotations
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
    .on 'click', =>
      if @canAnnotate and not @noBack and not @creatingHL
        setTimeout =>
          unless @selectedTargets?.length
            @hideFrame()
      delete @creatingHL
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

  showViewer: (viewName, annotations, focused = false) =>
    @panel?.notify
      method: "showViewer"
      params:
        view: viewName
        ids: (a.id for a in annotations when a.id)
        focused: focused

  toggleViewerSelection: (annotations, focused = false) =>
    @panel?.notify
      method: "toggleViewerSelection"
      params:
        ids: (a.id for a in annotations)
        focused: focused

  updateViewer: (viewName, annotations, focused = false) =>
    @panel?.notify
      method: "updateViewer"
      params:
        view: viewName
        ids: (a.id for a in annotations when a.id)
        focused: focused

  showEditor: (annotation) => @plugins.Bridge.showEditor annotation

  addEmphasis: (annotations) =>
    @panel?.notify
      method: "addEmphasis"
      params: (a.id for a in annotations when a.id)

  removeEmphasis: (annotations) =>
    @panel?.notify
      method: "removeEmphasis"
      params: (a.id for a in annotations when a.id)

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
    if @tool is 'highlight'

      # Describe the selection with targets
      @selectedTargets = (@_getTargetFromSelection(s) for s in event.segments)
      # Are we allowed to create annotations? Return false if we can't.
      unless @canAnnotate
        return false

      # Do we really want to make this selection?
      return false unless this.confirmSelection()

      # Add a flag about what's happening
      @creatingHL = true

      # Create the annotation
      annotation = {inject: true}
      this.publish 'beforeAnnotationCreated', annotation

      # Set up the annotation
      annotation = this.setupAnnotation annotation
      this.publish 'annotationCreated', annotation
    else
      super

  # Get the list of annotations impacted by a mouse event
  _getImpactedAnnotations: (event) ->
    # Get the raw list
    annotations = event.data.getAnnotations event

    # Are the highlights supposed to be visible?
    if (@tool is 'highlight') or @visibleHighlights
      # Just use the whole list
      annotations
    else
      # We need to check for focused annotations
      a for a in annotations when a in this.focusedAnnotations

  onAnchorMouseover: (event) ->
    this.addEmphasis this._getImpactedAnnotations event

  onAnchorMouseout: (event) ->
    this.removeEmphasis this._getImpactedAnnotations event

  # When clicking on a highlight in highlighting mode,
  # set @noBack to true to prevent the sidebar from closing
  onAnchorMousedown: (event) =>
    if this._getImpactedAnnotations(event).length
      @noBack = true

  # Select some annotations.
  #
  # toggle: should this toggle membership in an existing selection?
  # focus: should these annotation become focused?
  selectAnnotations: (annotations, toggle, focus) =>
    # Switch off dynamic mode; we are going to "Selection" scope
    @plugins.Heatmap.dynamicBucket = false

    if toggle
      # Tell sidebar to add these annotations to the sidebar
      this.toggleViewerSelection annotations, focus
    else
      # Tell sidebar to show the viewer for these annotations
      this.showViewer "Selection", annotations, focus

  # When clicking on a highlight in highlighting mode,
  # tell the sidebar to bring up the viewer for the relevant annotations
  onAnchorClick: (event) =>
    annotations = this._getImpactedAnnotations event
    return unless annotations.length and @noBack

    this.selectAnnotations annotations,
      (event.metaKey or event.ctrlKey), true

    # We have already prevented closing the sidebar, now reset this flag
    @noBack = false

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
    sel = @selectedTargets   # Save the selection
    # Nuke the selection, since we won't be using that.
    # We will attach this to the end of the document.
    # Our override for setupAnnotation will add that highlight.
    @selectedTargets = []
    this.onAdderClick()     # Open editor (with 0 targets)
    @selectedTargets = sel # restore the selection

  # Is this annotation a comment?
  isComment: (annotation) ->
    # No targets and no references means that this is a comment.
    not (annotation.inject or annotation.references?.length or annotation.target?.length)

  # Override for setupAnnotation, to handle comments
  setupAnnotation: (annotation) ->
    annotation = super # Set up annotation as usual
    if this.isComment annotation then @comments.push annotation
    annotation

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

  onAdderClick: (event) =>
    """
    Differs from upstream in a few ways:
    - Don't fire annotationCreated events: that's the job of the sidebar
    - Save the event for retriggering if login interrupts the flow
    """
    event?.preventDefault()

    # Save the event and targets for restarting edit on forced login
    @forcedLoginEvent = event
    @forcedLoginTargets = @selectedTargets

    # Hide the adder
    @adder.hide()
    @inAdderClick = false
    position = @adder.position()

    # Show a temporary highlight so the user can see what they selected
    # Also extract the quotation and serialize the ranges
    annotation = this.setupAnnotation(this.createAnnotation())

    hl.setTemporary(true) for hl in @getHighlights([annotation])

    # Subscribe to the editor events

    # Make the highlights permanent if the annotation is saved
    save = =>
      do cleanup
      hl.setTemporary false for hl in @getHighlights [annotation]

    # Remove the highlights if the edit is cancelled
    cancel = =>
      do cleanup
      this.deleteAnnotation(annotation)

    # Don't leak handlers at the end
    cleanup = =>
      this.unsubscribe('annotationEditorHidden', cancel)
      this.unsubscribe('annotationEditorSubmit', save)

    this.subscribe('annotationEditorHidden', cancel)
    this.subscribe('annotationEditorSubmit', save)

    # Display the editor.
    this.showEditor(annotation, position)

    # We have to clear the selection.
    # (Annotator does this automatically by focusing on
    # one of the input fields in the editor.)
    Annotator.util.getGlobal().getSelection().removeAllRanges()

  onSetTool: (name) ->
    switch name
      when 'comment'
        this.setVisibleHighlights this.visibleHighlights, false
      when 'highlight'
        this.setVisibleHighlights true, false

  onSetVisibleHighlights: (state) =>
    this.visibleHighlights = state
    this.setVisibleHighlights state, false

  # TODO: Workaround for double annotation deletion.
  # The short story: hiding the editor sometimes triggers
  # a spurious annotation delete.
  # Uncomment the traces below to investigate this further.
  deleteAnnotation: (annotation) ->
    if annotation.deleted
      return
    else
      annotation.deleted = true
    super
