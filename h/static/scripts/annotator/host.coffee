Annotator = require('annotator')
$ = Annotator.$

Hammer = require('hammerjs')

Guest = require('./guest')

# Minimum width to which the frame can be resized.
MIN_RESIZE = 280


module.exports = class Host extends Guest
  gestureState: null

  constructor: (element, options) ->
    src = options.app
    if options.firstRun
      # Allow options.app to contain query string params.
      src = src + (if '?' in src then '&' else '?') + 'firstrun'

    # Create the iframe
    app = $('<iframe></iframe>')
    .attr('name', 'hyp_sidebar_frame')
    .attr('seamless', '')
    .attr('src', src)

    @frame = $('<div></div>')
    .css('display', 'none')
    .addClass('annotator-frame annotator-outer annotator-collapsed')
    .appendTo(element)

    super
    this._addCrossFrameListeners()

    app.appendTo(@frame)

    if options.firstRun
      this.on 'panelReady', => this.showFrame(transition: false)

    # Host frame dictates the toolbar options.
    this.on 'panelReady', =>
      # Guest is designed to respond to events rather than direct method
      # calls. If we call set directly the other plugins will never recieve
      # these events and the UI will be out of sync.
      this.publish('setVisibleHighlights', !!options.showHighlights)

      # Time to actually show the UI
      @frame.css('display', '')

    if @plugins.BucketBar?
      this._setupGestures()
      @plugins.BucketBar.element.on 'click', (event) =>
        if @frame.hasClass 'annotator-collapsed'
          this.showFrame()

  destroy: ->
    @frame.remove()
    super

  showFrame: (options={transition: true}) ->
    if options.transition
      @frame.removeClass 'annotator-no-transition'
    else
      @frame.addClass 'annotator-no-transition'
    @frame.css 'margin-left': "#{-1 * @frame.width()}px"
    @frame.removeClass 'annotator-collapsed'

    if @toolbar?
      @toolbar.find('[name=sidebar-toggle]')
      .removeClass('h-icon-chevron-left')
      .addClass('h-icon-chevron-right')

  hideFrame: ->
    @frame.css 'margin-left': ''
    @frame.removeClass 'annotator-no-transition'
    @frame.addClass 'annotator-collapsed'

    if @toolbar?
      @toolbar.find('[name=sidebar-toggle]')
      .removeClass('h-icon-chevron-right')
      .addClass('h-icon-chevron-left')

  _addCrossFrameListeners: ->
    @crossframe.on('showFrame', this.showFrame.bind(this, null))
    @crossframe.on('hideFrame', this.hideFrame.bind(this, null))

  _initializeGestureState: ->
    @gestureState =
      acc: null
      initial: null
      renderFrame: null

  onPan: (event) =>
    # Smooth updates
    _updateLayout = =>
      # Only schedule one frame at a time
      return if @gestureState.renderFrame
      # Schedule update
      @gestureState.renderFrame = window.requestAnimationFrame =>
        # Clear the frame
        @gestureState.renderFrame = null
        # Stop if finished
        return unless @gestureState.acc?
        # Set style
        m = @gestureState.acc
        w = -m
        @frame.css('margin-left', "#{m}px")
        if w >= MIN_RESIZE then @frame.css('width', "#{-m}px")

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
        if @gestureState.acc <= -MIN_RESIZE
          this.showFrame()
        else
          this.hideFrame()
        # Reset the gesture state
        this._initializeGestureState()

      when 'panleft', 'panright'
        return unless @gestureState.initial?
        # Compute new margin from delta and initial conditions
        m = @gestureState.initial
        d = event.deltaX
        acc = Math.min(Math.round(m + d), 0)
        @gestureState.acc = acc
        # Start updating
        _updateLayout()

  onSwipe: (event) =>
    switch event.type
      when 'swipeleft'
        this.showFrame()
      when 'swiperight'
        this.hideFrame()

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
