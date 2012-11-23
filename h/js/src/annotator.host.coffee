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
        # Outside this closure, `this`, as it refers to the `easyXDM.Rpc`
        # object, is hidden, private to the `Rpc` object. Here, exploit access
        # to the `props` attribute to find the value of the iframe's src
        # attribute to be sure it is the iframe created by easyXDM.
        frame = $(this.container).find('[src^="'+@props.src+'"]')
          .css('visibility', 'visible')
        # Export the iframe element via the private `annotator` variable,
        # which references the `Annotator.Host` object.
        annotator.frame = frame
      swf: options.swf
      props:
        className: 'annotator-frame annotator-collapsed'
        style:
          visibility: 'hidden'
      remote: @app
    ,
      local:
        publish: (args..., k, fk) => this.publish args...
        setupAnnotation: => this.setupAnnotation arguments...
        onEditorHide: this.onEditorHide
        onEditorSubmit: this.onEditorSubmit
        showFrame: => @frame.removeClass('annotator-collapsed')
        hideFrame: => @frame.addClass('annotator-collapsed')
        resetFrameWidth: =>
          @frame.css({ "width": "", "margin-left" : "" })        
        setFrameWidth: (width) =>
          @frame.css({ "width": width, "margin-left" : (-1)*width })
        addtoFrameWidth: (width, innerWidth) =>
          if isNaN(parseInt(@frame[0].style.width)) then old = innerWidth else old = parseInt(@frame[0].style.width)
          @frame.css({ "width": (old + width), "margin-left" : (-1)*(old + width) })   
        getHighlights: =>
          highlights: $(@wrapper).find('.annotator-hl').map ->
            offset: $(this).offset()
            height: $(this).outerHeight(true)
            data: $(this).data('annotation').hash
          .get()
          offset: $(window).scrollTop()
        setActiveHighlights: (hashes=[]) =>
          @wrapper.find('.annotator-hl')
          .each ->
            if $(this).data('annotation').hash in hashes
              $(this).addClass('annotator-hl-active')
            else
              $(this).removeClass('annotator-hl-active')
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
        back: {}
        update: {}

  publish: (event, args) ->
    if event in ['annotationCreated']
      [annotation] = args
      @consumer.publish event, [annotation.hash]
    super arguments...

  _setupWrapper: ->
    @wrapper = @element
    .on 'mouseup', =>
      if not @ignoreMouseup
        setTimeout =>
          @consumer.back() unless @selectedRanges?.length
    this

  _setupDocumentEvents: ->
    # CSS "position: fixed" is hell of broken on most mobile devices
    # In this code, fixed is used *during* scroll on touch devices to prevent
    # jerky re-positioning of the sidebar. After scroll ends, the sidebar
    # is reset to "position: absolute" and positioned accordingly.
    timeout = null
    touch = false
    update = util.debounce =>
      unless touch
        @consumer.update()
        return
      if timeout then cancelTimeout timeout
      timeout = setTimeout =>
        timeout = null
        @frame?.css
          display: ''
          height: $(window).height()
          position: 'absolute'
          top: $(window).scrollTop()
        @consumer.update()
      , 400
    document.addEventListener 'touchmove', =>
      @frame?.css
        display: 'none'
      do update
    document.addEventListener 'touchstart', =>
      touch = true
      do update      
    $(window).on 'resize scroll', update
    $(document.body).on 'resize scroll', '*', util.debounce => @consumer.update()
    super

  # These methods aren't used in the iframe-hosted configuration of Annotator.
  _setupViewer: ->
    this

  _setupEditor: ->
    true

  showEditor: (annotation) =>
    stub =
      ranges: annotation.ranges
      quote: annotation.quote
      hash: annotation.hash
    if not stub.hash
      @consumer.createAnnotation (hash) =>
        annotation.hash = stub.hash = hash
        @consumer.showEditor stub
    else
      @consumer.showEditor stub

  checkForStartSelection: (event) =>
    # Annotator chokes on this callback hen trying to access
    # this.viewer.hide since there is no viewer. The `mouseIsDown` state
    # is needed for preventing the sidebar from closing while annotating.
    unless event and this.isAnnotator(event.target)
      @mouseIsDown = true
