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

    # Are going to be able to use the PDF plugin here?
    if window.PDFTextMapper?.applicable()
      # If we can, let's load the PDF plugin.
      @options.PDF = {}
    else
      # If we can't use the PDF plugin,
      # let's load the Document plugin instead.
      @options.Document = {}

    delete @options.app

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
        formatted.uri = @getHref()
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

  # Utility function to remove the hash part from a URL
  _removeHash: (url) ->
    url = new URL url
    url.hash = ""
    url.toString()

  # Utility function to get the decoded form of the document URI
  getRawHref: ->
    if @plugins.PDF
      @plugins.PDF.uri()
    else
      @plugins.Document.uri()

  # Utility function to get a de-hashed form of the document URI
  getHref: -> @_removeHash @getRawHref()

  # Utility function to filter metadata and de-hash the URIs
  getMetadata: =>
    metadata = @plugins.Document?.metadata
    metadata.link?.forEach (link) => link.href = @_removeHash link.href
    metadata

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
      (@plugins.PDF?.getMetaData() ? Promise.reject())
        .then (md) =>
           trans.complete
             uri: @getHref()
             metadata: md
        .catch (problem) =>
           trans.complete
             uri: @getHref()
             metadata: @getMetadata()
        .catch (e) ->

      trans.delayReturn(true)
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
    unless annotation.target?
      if @selectedRanges?
        annotation.target = (@_getTargetFromRange(r) for r in @selectedRanges)
        @selectedRanges = null
      else
        annotation.target = [this.getHref()]

    # Create a TextHighlight for a range.
    highlightRange = (range) =>
      normedRange = Annotator.Range.sniff(range).normalize(@element[0])
      return highlight.highlightRange(normedRange)

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

      this.plugins.CrossFrame.sync([annotation])

    # Anchor all the targets, highlighting the successes.
    promises = for target in annotation.target ? [] when target.selector
      this.anchorTarget(target)
      .then(highlightRange)
      .then(succeed(target), fail(target))

    # Collect the results.
    Promise.all(promises).then(finish)

    annotation

  createAnnotation: ->
    annotation = super
    this.plugins.CrossFrame.sync([annotation])
    annotation

  createHighlight: ->
    annotation = $highlight: true
    this.publish 'beforeAnnotationCreated', [annotation]
    this.plugins.CrossFrame.sync([annotation])
    annotation

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
        r = a.toRange(root)
        if quote?.exact? and r.toString() != quote.exact
          throw new Error('quote mismatch')
        else
          return r

    if range?
      promise = promise.catch =>
        a = anchor.RangeAnchor.fromSelector(range, root)
        r = a.toRange(root)
        if quote?.exact? and r.toString() != quote.exact
          throw new Error('quote mismatch')
        else
          return r

    if position?
      promise = promise.catch =>
        a = anchor.TextPositionAnchor.fromSelector(position)
        r = a.toRange(root)
        if quote?.exact? and r.toString() != quote.exact
          throw new Error('quote mismatch')
        else
          return r

    if quote?
      promise = promise.catch =>
        # The quote is implicitly checked during range conversion.
        a = anchor.TextQuoteAnchor.fromSelector(quote, position)
        r = a.toRange(root)

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

  # Create a target from a raw selection using all the anchor types.
  _getTargetFromRange: (range) ->
    selector = for type in ANCHOR_TYPES
      try
        type.fromRange(range).toSelector(@element[0])
      catch
        continue

    return {
      source: this.getHref()
      selector: selector
    }

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
        this.setupAnnotation(this.createHighlight())
      when 'comment'
        this.setupAnnotation(this.createAnnotation())
        this.triggerShowFrame()
    Annotator.Util.getGlobal().getSelection().removeAllRanges()
