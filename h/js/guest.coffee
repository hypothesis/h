$ = Annotator.$

class Annotator.Guest extends Annotator
  # Events to be bound on Annotator#element.
  events:
    ".annotator-adder button click":     "onAdderClick"
    ".annotator-adder button mousedown": "onAdderMousedown"
    ".annotator-hl mousedown": "onHighlightMousedown"
    ".annotator-hl click": "onHighlightClick"

  # Plugin configuration
  options:
    Document: {}

  # Internal state
  tool: 'comment'
  visibleHighlights: false

  constructor: (element, options) ->
    Gettext.prototype.parse_locale_data annotator_locale_data

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
        for k, v of annotation when k isnt 'highlights'
          formatted[k] = v
        formatted
      onConnect: (source, origin, scope) =>
        # Unfortunately, jschannel chokes on chrome-extension: origins
        if origin.match /^chrome-extension:\/\//
          origin = '*'

        @panel = this._setupXDM
          window: source
          origin: origin
          scope: "#{scope}:provider"
          onReady: =>
            console.log "Guest functions are ready for #{origin}"

    # Load plugins
    for own name, opts of @options
      if not @plugins[name]
        this.addPlugin(name, opts)

    # Scan the document text with the DOM Text libraries
    this.scanDocument "Annotator initialized"

  _setupXDM: (options) ->
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
      @wrapper.find('.annotator-hl')
      .each ->
        if $(this).data('annotation').$$tag in tags
          $(this).addClass('annotator-hl-active')
        else if not $(this).hasClass('annotator-hl-temporary')
          $(this).removeClass('annotator-hl-active')
    )

    .bind('scrollTo', (ctx, tag) =>
      @wrapper.find('.annotator-hl')
      .each ->
        if $(this).data('annotation').$$tag is tag
          $(this).scrollintoview()
    )

    .bind('adderClick', =>
      @onAdderClick @event
    )

    .bind('getDocumentInfo', =>
      return {
        uri: @plugins.Document.uri()
        metadata: @plugins.Document.metadata
      }
    )

    .bind('setTool', (ctx, name) => this.setTool name)

    .bind('setVisibleHighlights', (ctx, state) =>
      this.setVisibleHighlights state
    )

  scanDocument: (reason = "something happened") =>
    try
      console.log "Analyzing host frame, because " + reason + "..."
      r = this._scan()
      scanTime = r.time
      console.log "Traversal+scan took " + scanTime + " ms."
    catch e
      console.log e.message
      console.log e.stack

  _setupWrapper: ->
    @wrapper = @element
    .on 'click', =>
      unless @ignoreMouseup or @noBack
        setTimeout =>
          unless @selectedRanges?.length
            @panel?.notify method: 'back'
    this._setupMatching()
    @domMatcher.setRootNode @wrapper[0]
    this

  # These methods aren't used in the iframe-hosted configuration of Annotator.
  _setupViewer: -> this
  _setupEditor: -> this

  showViewer: (annotations) =>
    @panel?.notify method: "showViewer", params: (a.id for a in annotations)

  updateViewer: (annotations) =>
    @panel?.notify method: "updateViewer", params: (a.id for a in annotations)

  showEditor: (annotation) => @plugins.Bridge.showEditor annotation

  checkForStartSelection: (event) =>
    # Override to prevent Annotator choking when this ties to access the
    # viewer but preserve the manipulation of the attribute `mouseIsDown` which
    # is needed for preventing the panel from closing while annotating.
    unless event and this.isAnnotator(event.target)
      @mouseIsDown = true

  confirmSelection: ->
    return true unless @selectedRanges.length is 1

    target = this.getTargetFromRange @selectedRanges[0]
    selector = this.findSelector target.selector, "TextQuoteSelector"
    length = selector.exact.length

    if length > 2 then return true

    return confirm "You have selected a very short piece of text: only " + length + " chars. Are you sure you want to highlight this?"

  onSuccessfulSelection: (event) ->
    if @tool is 'highlight'

      # Do we really want to make this selection?
      return unless this.confirmSelection()

      # Create the annotation right away

      # Don't use the default method to create an annotation,
      # because we don't want to publish the beforeAnnotationCreated event
      # just yet.
      #
      # annotation = this.createAnnotation()
      #
      # Create an empty annotation manually instead
      annotation = {inject: true}

      annotation = this.setupAnnotation annotation
      $(annotation.highlights).addClass 'annotator-hl'

      # Notify listeners
      this.publish 'beforeAnnotationCreated', annotation
      this.publish 'annotationCreated', annotation
    else
      super event

  # When clicking on a highlight in highlighting mode,
  # set @noBack to true to prevent the sidebar from closing
  onHighlightMousedown: (event) =>
    if (@tool is 'highlight') or @visibleHighlights then @noBack = true

  # When clicking on a highlight in highlighting mode,
  # tell the sidebar to bring up the viewer for the relevant annotations
  onHighlightClick: (event) =>
    return unless (@tool is 'highlight') or @visibleHighlights and @noBack

    # Collect relevant annotations
    annotations = $(event.target)
      .parents('.annotator-hl')
      .addBack()
      .map -> return $(this).data("annotation")

    # Tell sidebar to show the viewer for these annotations
    this.showViewer annotations

    # We have already prevented closing the sidebar, now reset this flag
    @noBack = false

  setTool: (name) ->
    @tool = name
    @panel?.notify
      method: 'setTool'
      params: name

    switch name
      when 'comment'
        this.setVisibleHighlights this.visibleHighlights, true
      when 'highlight'
        this.setVisibleHighlights true, true

  setVisibleHighlights: (state=true, temporary=false) ->
    unless temporary
      @visibleHighlights = state
      @panel?.notify
        method: 'setVisibleHighlights'
        params: state

    markerClass = 'annotator-highlights-always-on'
    if state or (@tool is 'highlight')
      @element.addClass markerClass
    else
      @element.removeClass markerClass

  addComment: ->
    sel = @selectedRanges   # Save the selection
    # Nuke the selection, since we won't be using that.
    # We will attach this to the end of the document.
    # Our override for setupAnnotation will add that highlight.
    @selectedRanges = []
    this.onAdderClick()     # Open editor (with 0 targets)
    @selectedRanges = sel # restore the selection

  createFakeCommentRange: ->
    posSelector =
      type: "TextPositionSelector"
      start: @domMapper.corpus.length - 1
      end: @domMapper.corpus.length

    anchor = this.findAnchorFromPositionSelector selector: [posSelector]
    anchor.range

  # Override for setupAnnotation
  setupAnnotation: (annotation) ->
    # Set up annotation as usual
    annotation = super(annotation)
    # Does it have proper highlights?
    unless annotation.highlights?.length or annotation.references?.length or annotation.target?.length
      # No highlights and no references means that this is a comment,
      # or re-attachment has failed, but we'll skip orphaned annotations.

      # Get a fake range at the end of the document, and highlight it
      range = this.createFakeCommentRange()
      hl = this.highlightRange range

      # Register this highlight for the annotation, and vica versa
      $.merge annotation.highlights, hl
      $(hl).data('annotation', annotation)

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

    # Save the event for restarting edit
    @event = event

    # Hide the adder
    @adder.hide()
    position = @adder.position()

    # Show a temporary highlight so the user can see what they selected
    # Also extract the quotation and serialize the ranges
    annotation = this.setupAnnotation(this.createAnnotation())
    $(annotation.highlights).addClass('annotator-hl-temporary')

    # Subscribe to the editor events

    # Make the highlights permanent if the annotation is saved
    save = =>
      do cleanup
      $(annotation.highlights).removeClass('annotator-hl-temporary')

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
