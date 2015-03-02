$ = require('jquery')
Annotator = require('annotator')
Guest = require('./guest')


module.exports = class Annotator.Host extends Annotator.Guest
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
    this._addCrossFrameListeners()

    app.appendTo(@frame)

    if options.firstRun
      this.on 'panelReady', => this.showFrame(transition: false)

    # Host frame dictates the toolbar options.
    this.on 'panelReady', =>
      this.anchoring._scan() # Scan the document

      # Guest is designed to respond to events rather than direct method
      # calls. If we call set directly the other plugins will never recieve
      # these events and the UI will be out of sync.
      this.publish('setTool', 'comment')
      this.publish('setVisibleHighlights', !!options.showHighlights)

    if @plugins.BucketBar?
      this._setupDragEvents()
      @plugins.BucketBar.element.on 'click', (event) =>
        if @frame.hasClass 'annotator-collapsed'
          this.showFrame()

  showFrame: (options={transition: true}) ->
    unless @drag.enabled
      @frame.css 'margin-left': "#{-1 * @frame.width()}px"
    if options.transition
      @frame.removeClass 'annotator-no-transition'
    else
      @frame.addClass 'annotator-no-transition'
    @frame.removeClass 'annotator-collapsed'

  hideFrame: ->
      @frame.css 'margin-left': ''
      @frame.removeClass 'annotator-no-transition'
      @frame.addClass 'annotator-collapsed'

  _addCrossFrameListeners: ->
    @crossframe.on('showFrame', this.showFrame.bind(this, null))
    @crossframe.on('hideFrame', this.hideFrame.bind(this, null))

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
