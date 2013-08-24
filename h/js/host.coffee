$ = Annotator.$

class Annotator.Host extends Annotator.Guest
  # Drag state variables
  drag:
    delta: 0
    enabled: false
    last: null
    tick: false

  constructor: (element, options) ->
    # Create the iframe
    if document.baseURI and window.PDFView?
      # XXX: Hack around PDF.js resource: origin. Bug in jschannel?
      hostOrigin = '*'
    else
      hostOrigin = window.location.origin
      # XXX: Hack for missing window.location.origin in FF
      hostOrigin ?= window.location.protocol + "//" + window.location.host

    app = $('<iframe></iframe>')
    .attr('src', "#{options.app}#/?xdm=#{encodeURIComponent(hostOrigin)}")

    super

    app.appendTo(@frame)

    if @toolbar
      @toolbar.hide()
      app
      .on('mouseenter', => @toolbar.show())
      .on('mouseleave', => @toolbar.hide())

  _setupXDM: (options) ->
    channel = super
  # Set dynamic bucket mode on the sidebar
  setDynamicBucketMode: (value) ->
    @panel?.notify method: 'setDynamicBucketMode', params: value


    channel

    .bind('showFrame', =>
      @frame.css 'margin-left': "#{-1 * @frame.width()}px"
      @frame.removeClass 'annotator-no-transition'
      @frame.removeClass 'annotator-collapsed'
    )

    .bind('hideFrame', =>
      @frame.css 'margin-left': ''
      @frame.removeClass 'annotator-no-transition'
      @frame.addClass 'annotator-collapsed'
    )

    .bind('dragFrame', (ctx, screenX) =>
      if screenX > 0
        if @drag.last?
          @drag.delta += screenX - @drag.last
        @drag.last = screenX
      unless @drag.tick
        @drag.tick = true
        window.requestAnimationFrame this._dragRefresh
    )

    .bind('getMaxBottom', =>
      sel = '*' + (":not(.annotator-#{x})" for x in [
        'adder', 'outer', 'notice', 'filter', 'frame'
      ]).join('')

      # use the maximum bottom position in the page
      all = for el in $(document.body).find(sel)
        p = $(el).css('position')
        t = $(el).offset().top
        z = $(el).css('z-index')
        if (y = /\d+/.exec($(el).css('top'))?[0])
          t = Math.min(Number y, t)
        if (p == 'absolute' or p == 'fixed') and t == 0 and z != 'auto'
          bottom = $(el).outerHeight(false)
          # but don't go larger than 80, because this isn't bulletproof
          if bottom > 80 then 0 else bottom
        else
          0
      Math.max.apply(Math, all)
    )

    .bind('setDrag', (ctx, drag) =>
      @drag.enabled = drag
      @drag.last = null
    )

  _setupDocumentEvents: ->
    document.addEventListener 'dragover', (event) =>
      unless @drag.enabled then return
      if @drag.last?
        @drag.delta += event.screenX - @drag.last
      @drag.last = event.screenX
      unless @drag.tick
        @drag.tick = true
        window.requestAnimationFrame this._dragRefresh

    super

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

  showViewer: (annotations) =>
    @panel?.notify method: "showViewer", params: (a.id for a in annotations)

  updateViewer: (annotations) =>
    @panel?.notify method: "updateViewer", params: (a.id for a in annotations) 

  showEditor: (annotation) => @plugins.Bridge.showEditor annotation

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

    # Switch off dynamic bucket mode
    this.setDynamicBucketMode false

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
