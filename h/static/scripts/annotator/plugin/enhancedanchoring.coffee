Annotator = @Annotator
$ = Annotator.$

# Fake two-phase / pagination support, used for HTML documents
class DummyDocumentAccess

  @applicable: -> true
  getPageIndex: -> 0
  getPageCount: -> 1
  getPageIndexForPos: -> 0
  isPageMapped: -> true
  scan: ->

# Abstract anchor class.
class Anchor

  constructor: (@anchoring, @annotation, @target
      @startPage, @endPage,
      @quote, @diffHTML, @diffCaseOnly) ->

    unless @anchoring? then throw "anchoring manager is required!"
    unless @annotation? then throw "annotation is required!"
    unless @target? then throw "target is required!"
    unless @startPage? then "startPage is required!"
    unless @endPage? then throw "endPage is required!"
    unless @quote? then throw "quote is required!"

    @highlight = {}

  _getSegment: (page) ->
    throw "Function not implemented"

  # Create the missing highlights for this anchor
  realize: () =>
    return if @fullyRealized # If we have everything, go home

    # Collect the pages that are already rendered
    renderedPages = [@startPage .. @endPage].filter (index) =>
      @anchoring.document.isPageMapped index

    # Collect the pages that are already rendered, but not yet anchored
    pagesTodo = renderedPages.filter (index) => not @highlight[index]?

    return unless pagesTodo.length # Return if nothing to do

    # Create the new highlights
    created = for page in pagesTodo
      # TODO: add a layer of abstraction here
      # Don't call TextHighlight directly; instead, make a system
      # For registering highlight creators, or publish an event, or
      # whatever
      @highlight[page] = Annotator.TextHighlight.createFrom @_getSegment(page), this, page

    # Check if everything is rendered now
    @fullyRealized = renderedPages.length is @endPage - @startPage + 1

    # Announce the creation of the highlights
    @anchoring.annotator.publish 'highlightsCreated', created

  # Remove the highlights for the given set of pages
  virtualize: (pageIndex) =>
    highlight = @highlight[pageIndex]

    return unless highlight? # No highlight for this page

    highlight.removeFromDocument()

    delete @highlight[pageIndex]

    # Mark this anchor as not fully rendered
    @fullyRealized = false

    # Announce the removal of the highlight
    @anchoring.annotator.publish 'highlightRemoved', highlight

  # Virtualize and remove an anchor from all involved pages
  remove: ->
    # Go over all the pages
    for index in [@startPage .. @endPage]
      @virtualize index
      anchors = @anchoring.anchors[index]
      # Remove the anchor from the list
      i = anchors.indexOf this
      anchors[i..i] = []
      # Kill the list if it's empty
      delete @anchoring.anchors[index] unless anchors.length

Annotator.Anchor = Anchor

# This plugin contains the enhanced anchoring framework.
class Annotator.Plugin.EnhancedAnchoring extends Annotator.Plugin

  constructor: ->

  # Initializes the available document access strategies
  _setupDocumentAccessStrategies: ->
    @documentAccessStrategies = [
      # Default dummy strategy for simple HTML documents.
      # The generic fallback.
      name: "Dummy"
      mapper: DummyDocumentAccess
    ]

    this


  # Initializes the components used for analyzing the document
  chooseAccessPolicy: ->
    if @document? then return

    # Go over the available strategies
    for s in @documentAccessStrategies
      # Can we use this strategy for this document?
      if s.mapper.applicable()
        @documentAccessStrategy = s
        @document = new s.mapper()
        @anchors = {}
        addEventListener "docPageMapped", (evt) =>
          @_realizePage evt.pageIndex
        addEventListener "docPageUnmapped", (evt) =>
          @_virtualizePage evt.pageIndex
        s.init?()
        return this

  # Remove the current document access policy
  _removeCurrentAccessPolicy: ->
    return unless @document?

    list = @documentAccessStrategies
    index = list.indexOf @documentAccessStrategy
    list.splice(index, 1) unless index is -1

    @document.destroy?()
    delete @document

  # Perform a scan of the DOM. Required for finding anchors.
  _scan: ->
    # Ensure that we have a document access strategy
    @chooseAccessPolicy()
    try
      @pendingScan = @document.scan()
    catch
      @_removeCurrentAccessPolicy()
      @_scan()
      return

  # Plugin initialization
  pluginInit: ->
    @selectorCreators = []
    @strategies = []
    @_setupDocumentAccessStrategies()

    self = this
    @annotator.anchoring = this

    # Override loadAnnotations to account for the possibility that the anchoring
    # plugin is currently scanning the page.
    _loadAnnotations = Annotator.prototype.loadAnnotations
    Annotator.prototype.loadAnnotations = (annotations=[]) ->
      if self.pendingScan?
        # Schedule annotation load for when scan has finished
        self.pendingScan.then =>
          _loadAnnotations.call(this, annotations)
      else
        _loadAnnotations.call(this, annotations)

  # PUBLIC Try to find the right anchoring point for a given target
  #
  # Returns an Anchor object if succeeded, null otherwise
  createAnchor: (annotation, target) ->
    unless target?
      throw new Error "Trying to find anchor for null target!"

    error = null
    anchor = null
    for s in @strategies
      try
        a = s.code.call this, annotation, target
        if a
          # Store this anchor for the annotation
          annotation.anchors.push a

          # Store the anchor for all involved pages
          for pageIndex in [a.startPage .. a.endPage]
            @anchors[pageIndex] ?= []
            @anchors[pageIndex].push a

          # Realizing the anchor
          a.realize()

          return result: a
      catch error
        console.log "Strategy '" + s.name + "' has thrown an error.",
          error.stack ? error

    return error: "No strategies worked."

  # Do some normalization to get a "canonical" form of a string.
  # Used to even out some browser differences.
  normalizeString: (string) -> string.replace /\s{2,}/g, " "

  # Find the given type of selector from an array of selectors, if it exists.
  # If it does not exist, null is returned.
  findSelector: (selectors, type) ->
    for selector in selectors
      if selector.type is type then return selector
    null

  # Realize anchors on a given pages
  _realizePage: (index) ->
    # If the page is not mapped, give up
    return unless @document.isPageMapped index

    # Go over all anchors related to this page
    for anchor in @anchors[index] ? []
      anchor.realize()

  # Virtualize anchors on a given page
  _virtualizePage: (index) ->
    # Go over all anchors related to this page
    for anchor in @anchors[index] ? []
      anchor.virtualize index

  # Collect all the highlights (optionally for a given set of annotations)
  getHighlights: (annotations) ->
    results = []
    for anchor in @getAnchors(annotations)
      for page, highlight of anchor.highlight
        results.push highlight
    results

  # Collect all the anchors (optionally for a given set of annotations)
  getAnchors: (annotations) ->
    results = []
    if annotations?
      # Collect only the given set of annotations
      for annotation in annotations
        $.merge results, annotation.anchors
    else
      # Collect from everywhere
      for page, anchors of @anchors
        $.merge results, anchors
    results


  # PUBLIC entry point 1:
  # This is called to create a target from a raw selection,
  # using selectors created by the registered selector creators
  getSelectorsFromSelection: (selection) =>
    selectors = []
    for c in @selectorCreators
      description = c.describe selection
      for selector in description
        selectors.push selector

    selectors

