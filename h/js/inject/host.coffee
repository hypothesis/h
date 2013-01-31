$ = Annotator.$

util =
  debounce: (fn, delay=200) =>
      timer = null
      (args...) =>
        if timer then clearTimeout(timer)
        setTimeout =>
          timer = null
          fn args...
        , delay

class Annotator.Host extends Annotator
  # Events to be bound on Annotator#element.
  events:
    ".annotator-adder button click":     "onAdderClick"
    ".annotator-adder button mousedown": "onAdderMousedown"

  # Plugin configuration
  options: {}

  # timer used to throttle event frequency
  updateTimer: null

  # Drag state variables
  drag:
    delta: 0
    last: null
    tick: false

  constructor: (element, options) ->
    super

    @app = @options.app
    delete @options.app

    # Load plugins
    for own name, opts of @options
      if not @plugins[name]
        this.addPlugin(name, opts)

    # Grab this for exporting the iframe from easyXDM
    annotator = this

    # Establish cross-domain communication
    @consumer = new easyXDM.Rpc
      channel: 'annotator'
      container: @wrapper[0]
      local: options.local
      onReady: () ->
        # easyXDM updates this configuration object which provides access
        # to the `props` attribute to find the value of the iframe's src
        # attribute to find the iframe created by easyXDM.
        frame = $(this.container).find('[src^="'+@props.src+'"]')
          .css('visibility', 'visible')
        # Export the iframe element via the private `annotator` variable,
        # which references the `Annotator.Host` object.
        annotator.frame = frame
      swf: options.swf
      props:
        className: 'annotator-frame annotator-outer annotator-collapsed'
        style:
          visibility: 'hidden'
      remote: @app
    ,
      local:
        publish: (args..., k, fk) => this.publish args...
        setupAnnotation: => this.setupAnnotation arguments...
        deleteAnnotation: (annotation) =>
          toDelete = []
          @wrapper.find('.annotator-hl')
          .each ->
            data = $(this).data('annotation')
            if data.id == annotation.id and data not in toDelete
              toDelete.push data
          this.deleteAnnotation d for d in toDelete
        loadAnnotations: => this.loadAnnotations arguments...
        onEditorHide: this.onEditorHide
        onEditorSubmit: this.onEditorSubmit
        showFrame: =>
          @frame.css 'margin-left': "#{-1 * @frame.width()}px"
          @frame.removeClass 'annotator-no-transition'
          @frame.removeClass 'annotator-collapsed'
        hideFrame: =>
          @frame.css 'margin-left': ''
          @frame.removeClass 'annotator-no-transition'
          @frame.addClass 'annotator-collapsed'
        dragFrame: (screenX) =>
          if screenX > 0
            if @drag.last?
              @drag.delta += screenX - @drag.last
            @drag.last = screenX
          unless @drag.tick
            @drag.tick = true
            window.requestAnimationFrame this.dragRefresh
        getHighlights: =>
          highlights: $(@wrapper).find('.annotator-hl').map ->
            offset: $(this).offset()
            height: $(this).outerHeight(true)
            data: $(this).data('annotation')
          .get()
          offset: $(window).scrollTop()
        setActiveHighlights: (ids=[]) =>
          @wrapper.find('.annotator-hl')
          .each ->
            if $(this).data('annotation').id in ids
              $(this).addClass('annotator-hl-active')
            else if not $(this).hasClass('annotator-hl-temporary')
              $(this).removeClass('annotator-hl-active')
        getHref: =>
          uri = document.location.href
          if document.location.hash
            uri = uri.slice 0, (-1 * location.hash.length)
          $('meta[property^="og:url"]').each -> uri = this.content
          $('link[rel^="canonical"]').each -> uri = this.href
          return uri
        getMaxBottom: =>
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
        scrollTop: (y) =>
          $('html, body').stop().animate {scrollTop: y}, 600
      remote:
        publish: {}
        addPlugin: {}
        createAnnotation: {}
        showEditor: {}
        showViewer: {}
        back: {}
        update: {}

  _setupWrapper: ->
    @wrapper = @element
    .on 'mouseup', =>
      if not @ignoreMouseup
        setTimeout =>
          @consumer.back() unless @selectedRanges?.length
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
          @consumer.update()
    document.addEventListener 'touchmove', update
    document.addEventListener 'touchstart', =>
      touch = true
      @frame?.css
        display: 'none'
      do update
    document.addEventListener 'dragover', (event) =>
      if @drag.last?
        @drag.delta += event.screenX - @drag.last
      @drag.last = event.screenX
      unless @drag.tick
        @drag.tick = true
        window.requestAnimationFrame this.dragRefresh
    document.addEventListener 'dragleave', (event) =>
      if @drag.last?
        @drag.delta += event.screenX - @drag.last
      @drag.last = event.screenX
      unless @drag.tick
        @drag.tick = true
        window.requestAnimationFrame this.dragRefresh
    $(window).on 'resize scroll', update
    $(document.body).on 'resize scroll', '*', update
    super

  # These methods aren't used in the iframe-hosted configuration of Annotator.
  _setupViewer: ->
    this

  _setupEditor: ->
    true

  setupAnnotation: (annotation) ->
    annotation = super

    # Highlights are jQuery collections which have a circular references to the
    # annotation via data stored with `.data()`. Therefore, reconfigure the
    # property to hide them from serialization.
    Object.defineProperty annotation, 'highlights',
      enumerable: false

    annotation

  dragRefresh: =>
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

  showEditor: (annotation) =>
    if not annotation.id?
      @consumer.createAnnotation (id) =>
        if id?
          annotation.id = id
          @consumer.showEditor annotation
        else
          this.deleteAnnotation annotation
          @ignoreMouseup = false
    else
      @consumer.showEditor annotation

  checkForStartSelection: (event) =>
    # Override to prevent Annotator choking when this ties to access the
    # viewer but preserve the manipulation of the attribute `mouseIsDown` which
    # is needed for preventing the sidebar from closing while annotating.
    unless event and this.isAnnotator(event.target)
      @mouseIsDown = true
