$ = Annotator.$

class Annotator.Host extends Annotator
  # Events to be bound on Annotator#element.
  events:
    ".annotator-adder button click":     "onAdderClick"
    ".annotator-adder button mousedown": "onAdderMousedown"
    ".annotator-hl mousedown": "onHighlightMousedown"
    ".annotator-hl click": "onHighlightClick"

  # Plugin configuration
  options: {}

  # Drag state variables
  drag:
    delta: 0
    enabled: false
    last: null
    tick: false

  constructor: (element, options) ->
    Gettext.prototype.parse_locale_data annotator_locale_data    
    super

    @app = @options.app
    delete @options.app

    # Create the iframe
    if document.baseURI and window.PDFView?
      # XXX: Hack around PDF.js resource: origin. Bug in jschannel?
      hostOrigin = '*'
    else
      hostOrigin = window.location.origin
      # XXX: Hack for missing window.location.origin in FF
      hostOrigin ?= window.location.protocol + "//" + window.location.host

    @frame = $('<iframe></iframe>')
    .css(display: 'none')
    .attr('src', "#{@app}#/?xdm=#{encodeURIComponent(hostOrigin)}")
    .appendTo(@wrapper)
    .addClass('annotator-frame annotator-outer annotator-collapsed')
    .bind 'load', => this._setupXDM()

    # Load plugins
    for own name, opts of @options
      if not @plugins[name]
        this.addPlugin(name, opts)

    # Scan the document text with the DOM Text libraries
    this.scanDocument "Annotator initialized"

  setAlwaysOnHighlights: (value) ->
    body = $('body')
    markerClass = 'annotator-highlights-always-on'        
    if value
      body.addClass markerClass
    else
      body.removeClass markerClass        

  _setupXDM: ->
    # Set up the bridge plugin, which bridges the main annotation methods
    # between the host page and the panel widget.
    whitelist = ['diffHTML', 'quote', 'ranges', 'target', 'id']
    this.addPlugin 'Bridge',
      origin: '*'
      window: @frame[0].contentWindow
      formatter: (annotation) =>
        formatted = {}
        for k, v of annotation when k in whitelist
          formatted[k] = v
        formatted
      parser: (annotation) =>
        parsed = {}
        for k, v of annotation when k in whitelist
          parsed[k] = v
        parsed

    this.addPlugin 'Document'

    # Build a channel for the publish API
    @api = Channel.build
      origin: '*'
      scope: 'annotator:api'
      window: @frame[0].contentWindow

    # Build a channel for the panel UI
    @panel = Channel.build
      origin: '*'
      scope: 'annotator:panel'
      window: @frame[0].contentWindow
      onReady: =>
        @frame.css('display', '')

        @panel

        .bind('onEditorHide', this.onEditorHide)
        .bind('onEditorSubmit', this.onEditorSubmit)

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

        .bind('getHighlights', =>
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

        .bind('setHighlightingMode', (ctx, value) =>
          @highlightingMode = value
          this.setAlwaysOnHighlights value
        )

        .bind('getHref', => this.getHref())

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

        .bind('scrollTop', (ctx, y) =>
          $('html, body').stop().animate {scrollTop: y}, 600
        )

        .bind('setDrag', (ctx, drag) =>
          @drag.enabled = drag
          @drag.last = null
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
      unless @ignoreMouseup
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

    document.addEventListener 'touchmove', update
    document.addEventListener 'touchstart', =>
      touch = true
      @frame?.css
        display: 'none'
      do update

    document.addEventListener 'dragover', (event) =>
      unless @drag.enabled then return
      if @drag.last?
        @drag.delta += event.screenX - @drag.last
      @drag.last = event.screenX
      unless @drag.tick
        @drag.tick = true
        window.requestAnimationFrame this._dragRefresh

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

  showViewer: (annotations) => @plugins.Bridge.showViewer annotations
  showEditor: (annotation) => @plugins.Bridge.showEditor annotation

  checkForStartSelection: (event) =>
    # Override to prevent Annotator choking when this ties to access the
    # viewer but preserve the manipulation of the attribute `mouseIsDown` which
    # is needed for preventing the panel from closing while annotating.
    unless event and this.isAnnotator(event.target)
      @mouseIsDown = true

  onSuccessfulSelection: =>
    if @highlightingMode

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

    else
      super()

  # When clicking on a highlight, set @ignoreMouseup to true
  # to prevent the sidebar from closing
  onHighlightMousedown: (event) =>
    @ignoreMouseup = true

  onHighlightClick: (event) =>
    return unless @highlightingMode

    # We have already prevented closing the sidebar, now reset this flag
    @ignoreMouseup = false

    # Collect relevant annotations
    annotations = $(event.target)
      .parents('.annotator-hl')
      .andSelf()
      .map -> return $(this).data("annotation")

    # Tell sidebar to show the viewer for these annotations
    this.showViewer annotations

  addToken: (token) =>
    @api.notify
      method: 'addToken'
      params: token

  #Save the event for restarting edit
  onAdderClick: (event) =>
    @event = event
    super