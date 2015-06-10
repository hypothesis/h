raf = require('raf')
Promise = global.Promise ? require('es6-promise').Promise
Annotator = require('annotator')
$ = Annotator.$

anchoring = require('./anchoring/main')
highlighter = require('./highlighter')


module.exports = class Guest extends Annotator
  SHOW_HIGHLIGHTS_CLASS = 'annotator-highlights-always-on'

  # Events to be bound on Annotator#element.
  events:
    ".annotator-adder button click":     "onAdderClick"
    ".annotator-adder button mousedown": "onAdderMousedown"
    ".annotator-adder button mouseup":   "onAdderMouseup"
    ".annotator-hl click":               "onHighlightClick"
    ".annotator-hl mouseover":           "onHighlightMouseover"
    ".annotator-hl mouseout":            "onHighlightMouseout"
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

    this.anchors = []

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
    else if @plugins.Document?
      uriPromise = Promise.resolve(@plugins.Document.uri())
      metadataPromise = Promise.resolve(@plugins.Document.metadata)
    else
      uriPromise = Promise.reject()
      metadataPromise = Promise.reject()

    uriPromise = uriPromise.catch(-> decodeURIComponent(window.location.href))
    metadataPromise = metadataPromise.catch(-> {
      title: document.title
      link: [{href: decodeURIComponent(window.location.href)}]
    })

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
      for anchor in @anchors when anchor.highlights?
        toggle = anchor.annotation.$$tag in tags
        $(anchor.highlights).toggleClass('annotator-hl-focused', toggle)
    crossframe.on 'scrollToAnnotation', (ctx, tag) =>
      for anchor in @anchors when anchor.highlights?
        if anchor.annotation.$$tag is tag
          $(anchor.highlights).scrollintoview()
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
    self = this

    anchors = []
    anchoredTargets = []
    deadHighlights = []

    annotation.target ?= []

    locate = (target) ->
      options = {ignoreSelector: '[class^="annotator-"]'}
      return new Promise(raf)
      .then(-> anchoring.anchor(target.selector, options))
      .then((range) -> {annotation, target, range})
      .catch(-> {annotation, target})

    highlight = (anchor) ->
      if anchor.range?
        return new Promise(raf).then ->
          range = Annotator.Range.sniff(anchor.range)
          normedRange = range.normalize(self.element[0])
          highlights = highlighter.highlightRange(normedRange)
          rect = highlighter.getBoundingClientRect(highlights)
          anchor.highlights = highlights
          anchor.pos =
            left: rect.left + window.scrollX
            top: rect.top + window.scrollY
          return anchor
      return anchor

    sync = (anchors) ->
      annotation.$anchors = ({pos} for {pos} in anchors)
      annotation.$orphan = anchors.length > 0
      for anchor in anchors
        if anchor.range?
          annotation.$orphan = false

      self.anchors = self.anchors.concat(anchors)
      self.plugins.BucketBar?.update()
      self.plugins.CrossFrame?.sync([annotation])

    for anchor in self.anchors.splice(0, self.anchors.length)
      if anchor.annotation is annotation
        if anchor.range? and anchor.target in annotation.target
          anchors.push(anchor)
          anchoredTargets.push(anchor.target)
        else if anchor.highlights?
          deadHighlights.push(anchor.highlights)
          delete anchor.highlights
          delete anchor.range
      else
        self.anchors.push(anchor)

    deadHighlights = Array::concat(deadHighlights...)
    new Promise(raf).then(-> highlighter.removeHighlights(deadHighlights))

    for target in annotation.target when target not in anchoredTargets
      anchor = locate(target).then(highlight)
      anchors.push(anchor)

    Promise.all(anchors).then(sync)

    return annotation

  createAnnotation: (annotation = {}) ->
    ranges = @selectedRanges ? []
    @selectedRanges = null

    getSelectors = (range) ->
      options = {ignoreSelector: '[class^="annotator-"]'}
      return anchoring.describe(range, options)

    setDocumentInfo = ({metadata, uri}) ->
      annotation.uri = uri
      if metadata?
        annotation.document = metadata

    setTargets = ([info, selectors]) ->
      source = info.uri
      annotation.target = ({source, selector} for selector in selectors)

    info = this.getDocumentInfo().then(setDocumentInfo)
    selectors = Promise.all(ranges.map(getSelectors))
    targets = Promise.all([info, selectors]).then(setTargets)

    targets.then(=> this.setupAnnotation(annotation))
    targets.then(=> this.publish('beforeAnnotationCreated', [annotation]))

    annotation

  createHighlight: ->
    return this.createAnnotation({$highlight: true})

  deleteAnnotation: (annotation) ->
    anchors = []
    targets = []
    unhighlight = []

    for anchor in @anchors
      if anchor.annotation is annotation
        unhighlight.push(anchor.highlights ? [])
      else
        anchors.push(anchor)

    this.anchors = anchors
    this.publish('annotationDeleted', [annotation])
    this.plugins.BucketBar?.update()

    unhighlight = Array::concat(unhighlight...)
    new Promise(raf).then(-> highlighter.removeHighlights(unhighlight))

    return annotation

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

  onHighlightMouseover: (event) ->
    if @visibleHighlights
      event.stopPropagation()
      annotations = []
      for anchor in @anchors
        if event.target in (anchor.highlights ? [])
          annotations.push(anchor.annotation)
      this.focusAnnotations annotations

  onHighlightMouseout: (event) ->
    if @visibleHighlights
      event.stopPropagation()
      this.focusAnnotations []

  onHighlightClick: (event) =>
    if @visibleHighlights
      event.stopPropagation()
      annotations = []
      for anchor in @anchors
        if event.target in (anchor.highlights ? [])
          annotations.push(anchor.annotation)
      this.selectAnnotations annotations, (event.metaKey or event.ctrlKey)

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
