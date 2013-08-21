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

  constructor: (element, options) ->
    super

    # Load plugins
    for own name, opts of @options
      if not @plugins[name]
        this.addPlugin(name, opts)

    this.addPlugin 'Bridge',
      formatter: (annotation) =>
        formatted = {}
        if annotation.document?
          formatted['uri'] = @plugins.Document.uri()
        for k, v of annotation when k isnt 'highlights'
          formatted[k] = v
        formatted
      onConnect: (source, origin, scope) =>
        @panel = this._setupXDM
          window: source
          origin: origin
          scope: "#{scope}:provider"
          onReady: =>
            console.log "Guest functions are ready for #{origin}"

    # Scan the document text with the DOM Text libraries
    this.scanDocument "Annotator initialized"

  _setupXDM: (options) ->
    channel = Channel.build options

    channel

    .bind('onEditorHide', this.onEditorHide)
    .bind('onEditorSubmit', this.onEditorSubmit)

    .bind('getHighlights', =>
      console.log "XXX: Returning early from getHighlights"
      return
      highlights: $(@wrapper).find('.annotator-hl')
      .filter ->
        this.offsetWidth > 0 || this.offsetHeight > 0
      .map ->
        offset: $(this).offset()
        height: $(this).outerHeight(true)
        data: $(this).data('annotation').$$tag
      .get()
      offset: $(window).scrollTop()
    )

    .bind('setActiveHighlights', (ctx, tags=[]) =>
      @wrapper.find('.annotator-hl')
      .each ->
        if $(this).data('annotation').$$tag in tags
          $(this).addClass('annotator-hl-active')
        else if not $(this).hasClass('annotator-hl-temporary')
          $(this).removeClass('annotator-hl-active')
    )

    .bind('setAlwaysOnMode', (ctx, value) =>
      @alwaysOnMode = value
      this.setPersistentHighlights()
    )

    .bind('setHighlightingMode', (ctx, value) =>
      @highlightingMode = value
      if @highlightingMode then @adder.hide()
      this.setPersistentHighlights()
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

  scanDocument: (reason = "something happened") =>
    try
      console.log "Analyzing host frame, because " + reason + "..."
      r = @domMatcher.scan()
      scanTime = r.time
      console.log "Traversal+scan took " + scanTime + " ms."
    catch e
      console.log e.message
      console.log e.stack

  _setupWrapper: ->
    @wrapper = @element
    .on 'mouseup', =>
      if not @ignoreMouseup
        setTimeout =>
          unless @selectedRanges?.length then @panel?.notify method: 'back'
    this._setupMatching()
    @domMatcher.setRootNode @wrapper[0]
    this

  _setupDocumentEvents: ->
    tick = false
    timeout = null
    touch = false
    update = =>
      if touch
        # Defer updates on mobile until after touch events are over
        if timeout then cancelTimeout timeout
        timeout = setTimeout =>
          timeout = null
          do updateFrame
        , 400
      else
        do updateFrame
    updateFrame = =>
      unless tick
        tick = true
        requestAnimationFrame =>
          tick = false
          if touch
            # CSS "position: fixed" is hell of broken on most mobile devices
            @frame?.css
              display: ''
              height: $(window).height()
              position: 'absolute'
              top: $(window).scrollTop()
          @panel?.notify method: 'publish', params: 'hostUpdated'

    $(window).on 'resize scroll', update
    $(document.body).on 'resize scroll', '*', update

    if window.PDFView?
      # XXX: PDF.js hack
      $(PDFView.container).on 'scroll', update

    super

  # These methods aren't used in the iframe-hosted configuration of Annotator.
  _setupViewer: -> this
  _setupEditor: -> this

  _dragRefresh: =>
    d = @drag.delta
    @drag.delta = 0
    @drag.tick = false

    m = parseInt (getComputedStyle @frame[0]).marginLeft
    w = -1 * m
    m += d
    w -= d

    @frame.addClass 'annotator-no-transition'
    @frame.css
      'margin-left': "#{m}px"
      width: "#{w}px"

  showViewer: (annotation) => @plugins.Bridge.showViewer annotation
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
    if @highlightingMode

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
      annotation = {}

      annotation = this.setupAnnotation annotation
      $(annotation.highlights).addClass 'annotator-hl'

      # Tell the sidebar about the new annotation
      @plugins.Bridge.injectAnnotation annotation

      # Switch view to show the new annotation
      this.showViewer [ annotation ]
    else
      super event

  # When clicking on a highlight in highlighting mode,
  # set @noBack to true to prevent the sidebar from closing
  onHighlightMousedown: (event) =>
    if @highlightingMode or @alwaysOnMode then @noBack = true

  # When clicking on a highlight in highlighting mode,
  # tell the sidebar to bring up the viewer for the relevant annotations
  onHighlightClick: (event) =>
    return unless @highlightingMode or @alwaysOnMode and @noBack

    # We have already prevented closing the sidebar, now reset this flag
    @noBack = false

    # Collect relevant annotations
    annotations = $(event.target)
      .parents('.annotator-hl')
      .addBack()
      .map -> return $(this).data("annotation")

    # Tell sidebar to show the viewer for these annotations
    this.showViewer annotations

  setPersistentHighlights: ->
    body = $('body')
    markerClass = 'annotator-highlights-always-on'
    if @alwaysOnMode or @highlightingMode
      body.addClass markerClass
    else
      body.removeClass markerClass

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
