Promise = require('es6-promise').Promise
Annotator = require('annotator')
$ = Annotator.$

anchor = require('./lib/anchor')
highlight = require('./lib/highlight')

ANCHOR_TYPES = [
  anchor.FragmentAnchor
  anchor.RangeAnchor
  anchor.TextPositionAnchor
  anchor.TextQuoteAnchor
]


module.exports = class Guest extends Annotator
  SHOW_HIGHLIGHTS_CLASS = 'annotator-highlights-always-on'

  # Events to be bound on Annotator#element.
  events:
    ".annotator-adder button click":     "onAdderClick"
    ".annotator-adder button mousedown": "onAdderMousedown"
    ".annotator-adder button mouseup":   "onAdderMouseup"
    "setVisibleHighlights": "setVisibleHighlights"

  # Plugin configuration
  options:
    TextHighlights: {}
    TextSelection: {}

  # Internal state
  visibleHighlights: false

  html: jQuery.extend {}, Annotator::html,
    adder: '''
      <div class="annotator-adder">
        <button class="h-icon-insert-comment" data-action="comment" title="New Note"></button>
        <button class="h-icon-border-color" data-action="highlight" title="Highlight"></button>
      </div>
    '''

  constructor: (element, options, config = {}) ->
    super

    this.anchored = []
    this.unanchored = []

    cfOptions =
      on: (event, handler) =>
        this.subscribe(event, handler)
      emit: (event, args...) =>
        switch event
          # AnnotationSync tries to emit some events without taking actions.
          # We catch them and perform the right action (which will then emit
          # the event for real)
          when 'annotationDeleted'
            this.deleteAnnotation(args...)
          when 'loadAnnotations'
            this.loadAnnotations(args...)
          # Other events can simply be emitted.
          else
            this.publish(event, args)
      formatter: (annotation) =>
        formatted = {}
        for k, v of annotation when k isnt 'anchors'
          formatted[k] = v
        # Work around issue in jschannel where a repeated object is considered
        # recursive, even if it is not its own ancestor.
        if formatted.document?.title
          formatted.document.title = formatted.document.title.slice()
        formatted

    this.addPlugin('CrossFrame', cfOptions)
    @crossframe = this._connectAnnotationUISync(this.plugins.CrossFrame)

    # Load plugins
    for own name, opts of @options
      if not @plugins[name] and Annotator.Plugin[name]
        this.addPlugin(name, opts)

  # Get the document info
  getDocumentInfo: ->
    if @plugins.PDF?
      metadataPromise = Promise.resolve(@plugins.PDF.getMetadata())
      uriPromise = Promise.resolve(@plugins.PDF.uri())
    if @plugins.Document?
      uriPromise = Promise.resolve(@plugins.Document.uri())
      metadataPromise = Promise.resolve(@plugins.Document.metadata)

    return metadataPromise.then (metadata) =>
      return uriPromise.then (href) =>
        uri = new URL(href)
        uri.hash = ''
        uri = uri.toString()
        return {uri, metadata}

  _connectAnnotationUISync: (crossframe) ->
    crossframe.onConnect(=> this.publish('panelReady'))
    crossframe.on('onEditorHide', this.onEditorHide)
    crossframe.on('onEditorSubmit', this.onEditorSubmit)
    crossframe.on 'focusAnnotations', (ctx, tags=[]) =>
      for info in @anchored
        toggle = info.annotation.$$tag in tags
        $(info.highlights).toggleClass('annotator-hl-focused', toggle)
    crossframe.on 'scrollToAnnotation', (ctx, tag) =>
      for info in @anchored
        if info.annotation.$$tag is tag
          $(info.highlights).scrollintoview()
          return
    crossframe.on 'getDocumentInfo', (trans) =>
      trans.delayReturn(true)
      this.getDocumentInfo()
      .then((info) -> trans.complete(info))
      .catch((reason) -> trans.error(reason))
    crossframe.on 'setVisibleHighlights', (ctx, state) =>
      this.publish 'setVisibleHighlights', state

  _setupWrapper: ->
    @wrapper = @element
    .on 'click', (event) =>
      if !@selectedTargets?.length
        @triggerHideFrame()
    this

  # These methods aren't used in the iframe-hosted configuration of Annotator.
  _setupDynamicStyle: -> this
  _setupViewer: -> this
  _setupEditor: -> this
  _setupDocumentEvents: -> this

  destroy: ->
    $('#annotator-dynamic-style').remove()

    @adder.remove()

    @wrapper.find('.annotator-hl').each ->
      $(this).contents().insertBefore(this)
      $(this).remove()

    @element.data('annotator', null)

    for name, plugin of @plugins
      @plugins[name].destroy()

    this.removeEvents()

  setupAnnotation: (annotation) ->
    # Factories to close over the loop variable, below.
    succeed = (target) ->
      (highlights) -> {annotation, target, highlights}

    fail = (target) ->
      (reason) -> {annotation, target}

    # Function to collect anchoring promises
    finish = (results) =>
      anchored = false

      for result in results
        if result.highlights?
          anchored = true
          @anchored.push(result)
        else
          @unanchored.push(result)

      if results.length and not anchored
        annotation.$orphan = true

      # Sync the results
      this.plugins.CrossFrame.sync([annotation])

    # Create a TextHighlight for a range.
    highlightRange = (range) =>
      normedRange = Annotator.Range.sniff(range).normalize(@element[0])
      return highlight.highlightRange(normedRange)

    # Try to anchor all the targets
    anchorTargets = (targets = []) =>
      anchorPromises = for target in targets when target.selector
        try
          this.anchorTarget(target)
          .then(highlightRange)
          .then(succeed(target), fail(target))
        catch error
          Promise.reject(error).catch(fail(target))
      return Promise.all(anchorPromises).then(finish)

    # Start anchoring in the background
    anchorTargets(annotation.target)

    annotation

  createAnnotation: (annotation = {}) ->
    ranges = @selectedRanges
    @selectedRanges = null
    return this.getDocumentInfo().then (info) =>
      annotation.uri = info.uri
      this.createTargets(ranges).then (targets) =>
        annotation.target = targets
        this.publish('beforeAnnotationCreated', [annotation])
        return this.setupAnnotation(annotation)

  createHighlight: ->
    return this.createAnnotation({$highlight: true})

  deleteAnnotation: (annotation) ->
    for info in @anchored when info.annotation is annotation
      for h in info.highlights when h.parentNode?
        child = h.childNodes[0]
        $(h).replaceWith(h.childNodes)

    @anchored = (a for a in @anchored when a.annotation isnt annotation)
    @unanchored = (a for a in @unanchored when a.annotation isnt annotation)

    this.publish('annotationDeleted', [annotation])
    annotation

  ###*
  # Anchor a target.
  #
  # This function converts an annotation target into a document range using
  # its selectors. It encapsulates the core anchoring algorithm that uses the
  # selectors alone or in combination to establish an anchor within the document.
  #
  # :root Node target: The root Node of the anchoring context.
  # :param Object target: The target to anchor.
  # :return: A Promise that resolves to a Range on success.
  # :rtype: Promise
  ####
  anchorTarget: (target) ->
    root = @element[0]

    # Selectors
    fragment = null
    position = null
    quote = null
    range = null

    # Collect all the selectors
    for selector in target.selector ? []
      switch selector.type
        when 'FragmentSelector'
          fragment = selector
        when 'TextPositionSelector'
          position = selector
        when 'TextQuoteSelector'
          quote = selector
        when 'RangeSelector'
          range = selector

    # Until we successfully anchor, we fail.
    promise = Promise.reject('unable to anchor')

    if fragment?
      promise = promise.catch =>
        a = anchor.FragmentAnchor.fromSelector(fragment)
        Promise.resolve(a).then (a) ->
          Promise.resolve(a.toRange(root)).then (r) ->
            if quote?.exact? and r.toString() != quote.exact
              throw new Error('quote mismatch')
            else
              return r

    if range?
      promise = promise.catch =>
        a = anchor.RangeAnchor.fromSelector(range, root)
        Promise.resolve(a).then (a) ->
          Promise.resolve(a.toRange(root)).then (r) ->
            if quote?.exact? and r.toString() != quote.exact
              throw new Error('quote mismatch')
            else
              return r

    if position?
      promise = promise.catch =>
        a = anchor.TextPositionAnchor.fromSelector(position)
        Promise.resolve(a).then (a) ->
          Promise.resolve(a.toRange(root)).then (r) ->
            if quote?.exact? and r.toString() != quote.exact
              throw new Error('quote mismatch')
            else
              return r

    if quote?
      promise = promise.catch =>
        # The quote is implicitly checked during range conversion.
        a = anchor.TextQuoteAnchor.fromSelector(quote, position)
        Promise.resolve(a).then (a) ->
          Promise.resolve(a.toRange(root))

    return promise

  showAnnotations: (annotations) =>
    @crossframe?.notify
      method: "showAnnotations"
      params: (a.$$tag for a in annotations)

  toggleAnnotationSelection: (annotations) =>
    @crossframe?.notify
      method: "toggleAnnotationSelection"
      params: (a.$$tag for a in annotations)

  updateAnnotations: (annotations) =>
    @crossframe?.notify
      method: "updateAnnotations"
      params: (a.$$tag for a in annotations)

  focusAnnotations: (annotations) =>
    @crossframe?.notify
      method: "focusAnnotations"
      params: (a.$$tag for a in annotations)

  onAnchorMousedown: ->

  createTargets: (ranges) ->
    info = this.getDocumentInfo()
    if ranges?
      targets = ranges.map (range) =>
        this.createSelectors(range).then (selectors) =>
          info.then (info) =>
            return {
              source: info.uri
              selector: selectors
            }
    else
      targets = [info.then(({uri}) -> {source: uri})]

    return Promise.all(targets)

  createSelectors: (range) ->
    root = @element[0]
    toSelector = (anchor) -> anchor.toSelector(root)
    softFail = (reason) -> null
    notNull = (selectors) -> (s for s in selectors when s?)
    selectors = ANCHOR_TYPES.map (type) =>
      try
        Promise.resolve(type.fromRange(range)).then (a) ->
          Promise.resolve(a.toSelector(root))
        , softFail
      catch
        Promise.resolve()
    return Promise.all(selectors).then(notNull)

  onSuccessfulSelection: (event, immediate) ->
    unless event?
      throw "Called onSuccessfulSelection without an event!"
    unless event.ranges?
      throw "Called onSuccessulSelection with an event with missing ranges!"

    @selectedRanges = event.ranges

    # Do we want immediate annotation?
    if immediate
      # Create an annotation
      @onAdderClick event
    else
      # Show the adder button
      @adder
        .css(Annotator.Util.mousePosition(event, @wrapper[0]))
        .show()

    true

  onFailedSelection: (event) ->
    @adder.hide()
    @selectedRanges = []

  # Select some annotations.
  #
  # toggle: should this toggle membership in an existing selection?
  selectAnnotations: (annotations, toggle) =>
    if toggle
      # Tell sidebar to add these annotations to the sidebar if not already
      # selected, otherwise remove them.
      this.toggleAnnotationSelection annotations
    else
      # Tell sidebar to show the viewer for these annotations
      this.triggerShowFrame()
      this.showAnnotations annotations

  # When Mousing over a highlight, tell the sidebar to focus the relevant annotations
  onAnchorMouseover: (event) ->
    if @visibleHighlights
      event.stopPropagation()
      annotations = event.data.getAnnotations(event)
      this.focusAnnotations annotations

  # Tell the sidebar to stop highlighting the relevant annotations
  onAnchorMouseout: (event) ->
    if @visibleHighlights
      event.stopPropagation()
      this.focusAnnotations []

  # When clicking on a highlight, tell the sidebar to bring up the viewer for the relevant annotations
  onAnchorClick: (event) =>
    if @visibleHighlights
      event.stopPropagation()
      this.selectAnnotations (event.data.getAnnotations event),
        (event.metaKey or event.ctrlKey)

  # Pass true to show the highlights in the frame or false to disable.
  setVisibleHighlights: (shouldShowHighlights) ->
    return if @visibleHighlights == shouldShowHighlights

    @crossframe?.notify
      method: 'setVisibleHighlights'
      params: shouldShowHighlights

    this.toggleHighlightClass(shouldShowHighlights)

  toggleHighlightClass: (shouldShowHighlights) ->
    if shouldShowHighlights
      @element.addClass(SHOW_HIGHLIGHTS_CLASS)
    else
      @element.removeClass(SHOW_HIGHLIGHTS_CLASS)

    @visibleHighlights = shouldShowHighlights

  # Open the sidebar
  triggerShowFrame: ->
    @crossframe?.notify method: 'open'

  # Close the sidebar
  triggerHideFrame: ->
    @crossframe?.notify method: 'back'

  onAdderMouseup: (event) ->
    event.preventDefault()
    event.stopPropagation()

  onAdderMousedown: ->

  onAdderClick: (event) =>
    event.preventDefault?()
    event.stopPropagation?()
    @adder.hide()
    switch event.target.dataset.action
      when 'highlight'
        this.setVisibleHighlights true
        this.createHighlight()
      when 'comment'
        this.createAnnotation()
        this.triggerShowFrame()
    Annotator.Util.getGlobal().getSelection().removeAllRanges()
