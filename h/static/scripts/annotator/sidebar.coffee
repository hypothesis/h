extend = require('extend')
raf = require('raf')
Hammer = require('hammerjs')

Host = require('./host')

# Minimum width to which the frame can be resized.
MIN_RESIZE = 80


module.exports = class Sidebar extends Host
  options:
    Document: {}
    TextSelection: {}
    BucketBar:
      container: '.annotator-frame'
    Toolbar:
      container: '.annotator-frame'

  renderFrame: null
  gestureState: null

  constructor: (element, options) ->
    super
    this.hide()

    if options.firstRun
      this.on 'panelReady', => this.show()

    if @plugins.BucketBar?
      @plugins.BucketBar.element.on 'click', (event) => this.show()

    if @plugins.Toolbar?
      this._setupGestures()

    this._setupSidebarEvents()

  _setupDocumentEvents: ->
    @element.on 'click', (event) =>
      if !@selectedTargets?.length
        this.hide()
    return this

  _setupSidebarEvents: ->
    @crossframe.on('show', this.show.bind(this))
    @crossframe.on('hide', this.hide.bind(this))

    # Return this for chaining
    this

  _setupGestures: ->
    $toggle = @toolbar.find('[name=sidebar-toggle]')

    # Prevent any default gestures on the handle
    $toggle.on('touchmove', (event) -> event.preventDefault())

    # Set up the Hammer instance and handlers
    mgr = new Hammer.Manager($toggle[0])
    .on('panstart panend panleft panright', this.onPan)
    .on('swipeleft swiperight', this.onSwipe)

    # Set up the gesture recognition
    pan = mgr.add(new Hammer.Pan({direction: Hammer.DIRECTION_HORIZONTAL}))
    swipe = mgr.add(new Hammer.Swipe({direction: Hammer.DIRECTION_HORIZONTAL}))
    swipe.recognizeWith(pan)

    # Set up the initial state
    this._initializeGestureState()

    # Return this for chaining
    this

  _initializeGestureState: ->
    @gestureState =
      initial: null
      final: null

  # Schedule any changes needed to update the sidebar layout.
  _updateLayout: ->
    # Only schedule one frame at a time
    return if @renderFrame

    # Schedule a frame
    @renderFrame = raf =>
      @renderFrame = null  # Clear the schedule

      # Process the resize gesture
      if @gestureState.final isnt @gestureState.initial
        m = @gestureState.final
        w = -m
        @frame.css('margin-left', "#{m}px")
        if w >= MIN_RESIZE then @frame.css('width', "#{w}px")

  onPan: (event) =>
    switch event.type
      when 'panstart'
        # Initialize the gesture state
        this._initializeGestureState()
        # Immadiate response
        @frame.addClass 'annotator-no-transition'
        # Escape iframe capture
        @frame.css('pointer-events', 'none')
        # Set origin margin
        @gestureState.initial = parseInt(getComputedStyle(@frame[0]).marginLeft)

      when 'panend'
        # Re-enable transitions
        @frame.removeClass 'annotator-no-transition'
        # Re-enable iframe events
        @frame.css('pointer-events', '')
        # Snap open or closed
        if @gestureState.final <= -MIN_RESIZE
          this.show()
        else
          this.hide()
        # Reset the gesture state
        this._initializeGestureState()

      when 'panleft', 'panright'
        return unless @gestureState.initial?
        # Compute new margin from delta and initial conditions
        m = @gestureState.initial
        d = event.deltaX
        @gestureState.final = Math.min(Math.round(m + d), 0)
        # Start updating
        this._updateLayout()

  onSwipe: (event) =>
    switch event.type
      when 'swipeleft'
        this.show()
      when 'swiperight'
        this.hide()

  show: ->
    @frame.css 'margin-left': "#{-1 * @frame.width()}px"
    @frame.removeClass 'annotator-collapsed'

    if @toolbar?
      @toolbar.find('[name=sidebar-toggle]')
      .removeClass('h-icon-chevron-left')
      .addClass('h-icon-chevron-right')

  hide: ->
    @frame.css 'margin-left': ''
    @frame.addClass 'annotator-collapsed'

    if @toolbar?
      @toolbar.find('[name=sidebar-toggle]')
      .removeClass('h-icon-chevron-right')
      .addClass('h-icon-chevron-left')

  createAnnotation: (annotation = {}) ->
    super
    this.show() unless annotation.$highlight

  showAnnotations: (annotations) ->
    super
    this.show()
