Annotator = @Annotator
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

    src = options.app
    if options.firstRun
      # Allow options.app to contain query string params.
      src = src + (if '?' in src then '&' else '?') + 'firstrun'

    app = $('<iframe></iframe>')
    .attr('name', 'hyp_sidebar_frame')
    .attr('seamless', '')
    .attr('src', src)

    super element, options, dontScan: true

    app.appendTo(@frame)

    if options.firstRun
      this.on 'panelReady', => this.actuallyShowFrame(transition: false)

    # Host frame dictates the toolbar options.
    this.on 'panelReady', =>
      this.setTool('comment')
      this._scan() # Scan the document
      this.setVisibleHighlights(!!options.showHighlights)

    if @plugins.BucketBar?
      this._setupDragEvents()
      @plugins.BucketBar.element.on 'click', (event) =>
        if @frame.hasClass 'annotator-collapsed'
          this.showFrame()

  actuallyShowFrame: (options={transition: true}) ->
    unless @drag.enabled
      @frame.css 'margin-left': "#{-1 * @frame.width()}px"
    if options.transition
      @frame.removeClass 'annotator-no-transition'
    else
      @frame.addClass 'annotator-no-transition'
    @frame.removeClass 'annotator-collapsed'

  _setupXDM: (options) ->
    channel = super

    channel

    .bind 'showFrame', (ctx) => this.actuallyShowFrame()

    .bind('hideFrame', (ctx) =>
      @frame.css 'margin-left': ''
      @frame.removeClass 'annotator-no-transition'
      @frame.addClass 'annotator-collapsed'
    )

    .bind('dragFrame', (ctx, screenX) => this._dragUpdate screenX)

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

  _setupDragEvents: ->
    el = document.createElementNS 'http://www.w3.org/1999/xhtml', 'canvas'
    el.width = el.height = 1
    @element.append el

    dragStart = (event) =>
      event.dataTransfer.dropEffect = 'none'
      event.dataTransfer.effectAllowed = 'none'
      event.dataTransfer.setData 'text/plain', ''
      event.dataTransfer.setDragImage el, 0, 0
      @drag.enabled = true
      @drag.last = event.screenX

      m = parseInt (getComputedStyle @frame[0]).marginLeft
      @frame.css
        'margin-left': "#{m}px"
      this.showFrame()

    dragEnd = (event) =>
      @drag.enabled = false
      @drag.last = null

    for handle in [@plugins.BucketBar.element[0], @plugins.Toolbar.buttons[0]]
      handle.draggable = true
      handle.addEventListener 'dragstart', dragStart
      handle.addEventListener 'dragend', dragEnd

    document.addEventListener 'dragover', (event) =>
      this._dragUpdate event.screenX

  _dragUpdate: (screenX) =>
    unless @drag.enabled then return
    if @drag.last?
      @drag.delta += screenX - @drag.last
    @drag.last = screenX
    unless @drag.tick
      @drag.tick = true
      window.requestAnimationFrame this._dragRefresh

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
