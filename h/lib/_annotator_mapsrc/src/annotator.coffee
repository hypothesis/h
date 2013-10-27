# Selection and range creation reference for the following code:
# http://www.quirksmode.org/dom/range_intro.html
#
# I've removed any support for IE TextRange (see commit d7085bf2 for code)
# for the moment, having no means of testing it.

util =
  uuid: (-> counter = 0; -> counter++)()

  getGlobal: -> (-> this)()

  # Return the maximum z-index of any element in $elements (a jQuery collection).
  maxZIndex: ($elements) ->
    all = for el in $elements
            if $(el).css('position') == 'static'
              -1
            else
              parseInt($(el).css('z-index'), 10) or -1
    Math.max.apply(Math, all)

  mousePosition: (e, offsetEl) ->
    # If the offset element is not a positioning root use its offset parent
    unless $(offsetEl).css('position') in ['absolute', 'fixed', 'relative']
      offsetEl = $(offsetEl).offsetParent()[0]
    offset = $(offsetEl).offset()
    {
      top:  e.pageY - offset.top,
      left: e.pageX - offset.left
    }

  # Checks to see if an event parameter is provided and contains the prevent
  # default method. If it does it calls it.
  #
  # This is useful for methods that can be optionally used as callbacks
  # where the existance of the parameter must be checked before calling.
  preventEventDefault: (event) ->
    event?.preventDefault?()

# Store a reference to the current Annotator object.
_Annotator = this.Annotator

class Annotator extends Delegator
  # Events to be bound on Annotator#element.
  events:
    ".annotator-adder button click":     "onAdderClick"
    ".annotator-adder button mousedown": "onAdderMousedown"
    ".annotator-hl mouseover":           "onHighlightMouseover"
    ".annotator-hl mouseout":            "startViewerHideTimer"

  html:
    adder:   '<div class="annotator-adder"><button>' + _t('Annotate') + '</button></div>'
    wrapper: '<div class="annotator-wrapper"></div>'

  options: # Configuration options
    readOnly: false # Start Annotator in read-only mode. No controls will be shown.

  plugins: {}

  editor: null

  viewer: null

  selectedRanges: null

  mouseIsDown: false

  ignoreMouseup: false

  viewerHideTimer: null

  # Public: Creates an instance of the Annotator. Requires a DOM Element in
  # which to watch for annotations as well as any options.
  #
  # NOTE: If the Annotator is not supported by the current browser it will not
  # perform any setup and simply return a basic object. This allows plugins
  # to still be loaded but will not function as expected. It is reccomended
  # to call Annotator.supported() before creating the instance or using the
  # Unsupported plugin which will notify users that the Annotator will not work.
  #
  # element - A DOM Element in which to annotate.
  # options - An options Object. NOTE: There are currently no user options.
  #
  # Examples
  #
  #   annotator = new Annotator(document.body)
  #
  #   # Example of checking for support.
  #   if Annotator.supported()
  #     annotator = new Annotator(document.body)
  #   else
  #     # Fallback for unsupported browsers.
  #
  # Returns a new instance of the Annotator.
  constructor: (element, options) ->
    super
    @plugins = {}

    # Return early if the annotator is not supported.
    return this unless Annotator.supported()
    this._setupDocumentEvents() unless @options.readOnly
    this._setupWrapper()
    this._setupMatching() unless @options.noMatching
    this._setupViewer()._setupEditor()
    this._setupDynamicStyle()

    # Perform initial DOM scan, unless told not to.
    this._scan() unless (@options.noScan or @options.noMatching)

    # Create adder
    this.adder = $(this.html.adder).appendTo(@wrapper).hide()

  # Initializes the components used for analyzing the DOM
  _setupMatching: ->
        
    @domMapper = new DomTextMapper()
    @domMatcher = new DomTextMatcher @domMapper
    @domMapper.setRootNode @wrapper[0]

    this

  # Perform a scan of the DOM. Required for finding anchors.
  _scan: ->
    @domMatcher.scan()   
 
  # Wraps the children of @element in a @wrapper div. NOTE: This method will also
  # remove any script elements inside @element to prevent them re-executing.
  #
  # Returns itself to allow chaining.
  _setupWrapper: ->
    @wrapper = $(@html.wrapper)

    # We need to remove all scripts within the element before wrapping the
    # contents within a div. Otherwise when scripts are reappended to the DOM
    # they will re-execute. This is an issue for scripts that call
    # document.write() - such as ads - as they will clear the page.
    @element.find('script').remove()
    @element.wrapInner(@wrapper)
    @wrapper = @element.find('.annotator-wrapper')

    this

  # Creates an instance of Annotator.Viewer and assigns it to the @viewer
  # property, appends it to the @wrapper and sets up event listeners.
  #
  # Returns itself to allow chaining.
  _setupViewer: ->
    @viewer = new Annotator.Viewer(readOnly: @options.readOnly)
    @viewer.hide()
      .on("edit", this.onEditAnnotation)
      .on("delete", this.onDeleteAnnotation)
      .addField({
        load: (field, annotation) =>
          if annotation.text
            $(field).html(Util.escape(annotation.text))
          else
            $(field).html("<i>#{_t 'No Comment'}</i>")
          this.publish('annotationViewerTextField', [field, annotation])
      })
      .element.appendTo(@wrapper).bind({
        "mouseover": this.clearViewerHideTimer
        "mouseout":  this.startViewerHideTimer
      })
    this

  # Creates an instance of the Annotator.Editor and assigns it to @editor.
  # Appends this to the @wrapper and sets up event listeners.
  #
  # Returns itself for chaining.
  _setupEditor: ->
    @editor = new Annotator.Editor()
    @editor.hide()
      .on('hide', this.onEditorHide)
      .on('save', this.onEditorSubmit)
      .addField({
        type: 'textarea',
        label: _t('Comments') + '\u2026'
        load: (field, annotation) ->
          $(field).find('textarea').val(annotation.text || '')
        submit: (field, annotation) ->
          annotation.text = $(field).find('textarea').val()
      })

    @editor.element.appendTo(@wrapper)
    this

  # Sets up the selection event listeners to watch mouse actions on the document.
  #
  # Returns itself for chaining.
  _setupDocumentEvents: ->
    $(document).bind({
      "mouseup":   this.checkForEndSelection
      "mousedown": this.checkForStartSelection
    })
    this

  # Sets up any dynamically calculated CSS for the Annotator.
  #
  # Returns itself for chaining.
  _setupDynamicStyle: ->
    style = $('#annotator-dynamic-style')

    if (!style.length)
      style = $('<style id="annotator-dynamic-style"></style>').appendTo(document.head)

    sel = '*' + (":not(.annotator-#{x})" for x in ['adder', 'outer', 'notice', 'filter']).join('')

    # use the maximum z-index in the page
    max = util.maxZIndex($(document.body).find(sel))

    # but don't go smaller than 1010, because this isn't bulletproof --
    # dynamic elements in the page (notifications, dialogs, etc.) may well
    # have high z-indices that we can't catch using the above method.
    max = Math.max(max, 1000)

    style.text [
      ".annotator-adder, .annotator-outer, .annotator-notice {"
      "  z-index: #{max + 20};"
      "}"
      ".annotator-filter {"
      "  z-index: #{max + 10};"
      "}"
    ].join("\n")

    this

  getHref: =>
    uri = decodeURIComponent document.location.href
    if document.location.hash then uri = uri.slice 0, (-1 * location.hash.length)
    $('meta[property^="og:url"]').each -> uri = decodeURIComponent this.content
    $('link[rel^="canonical"]').each -> uri = decodeURIComponent this.href
    return uri

  getRangeSelector: (range) ->
    sr = range.serialize @wrapper[0]
    selector =
      type: "RangeSelector"
      startContainer: sr.startContainer
      startOffset: sr.startOffset
      endContainer: sr.endContainer
      endOffset: sr.endOffset

  getTextQuoteSelector: (range) ->
    unless range?
      throw new Error "Called getTextQuoteSelector(range) with null range!"

    rangeStart = range.start
    unless rangeStart?
      throw new Error "Called getTextQuoteSelector(range) on a range with no valid start."
    startOffset = (@domMapper.getInfoForNode rangeStart).start
    rangeEnd = range.end
    unless rangeEnd?
      throw new Error "Called getTextQuoteSelector(range) on a range with no valid end."
    endOffset = (@domMapper.getInfoForNode rangeEnd).end

    quote = @domMapper.getContentForCharRange startOffset, endOffset
    [prefix, suffix] = @domMapper.getContextForCharRange startOffset, endOffset
    selector =
      type: "TextQuoteSelector"
      exact: quote
      prefix: prefix
      suffix: suffix

  getTextPositionSelector: (range) ->
    startOffset = (@domMapper.getInfoForNode range.start).start
    endOffset = (@domMapper.getInfoForNode range.end).end

    selector =
      type: "TextPositionSelector"
      start: startOffset
      end: endOffset

  getQuoteForTarget: (target) ->
    selector = this.findSelector target.selector, "TextQuoteSelector"
    if selector?
      this.normalizeString selector.exact
    else
      null

  # Public: Gets the current selection excluding any nodes that fall outside of
  # the @wrapper. Then returns and Array of NormalizedRange instances.
  #
  # Examples
  #
  #   # A selection inside @wrapper
  #   annotation.getSelectedRanges()
  #   # => Returns [NormalizedRange]
  #
  #   # A selection outside of @wrapper
  #   annotation.getSelectedRanges()
  #   # => Returns []
  #
  # Returns Array of NormalizedRange instances.
  getSelectedRanges: ->
    selection = util.getGlobal().getSelection()

    ranges = []
    rangesToIgnore = []
    unless selection.isCollapsed
      ranges = for i in [0...selection.rangeCount]
        r = selection.getRangeAt(i)
        browserRange = new Range.BrowserRange(r)
        normedRange = browserRange.normalize().limit(@wrapper[0])

        # If the new range falls fully outside the wrapper, we
        # should add it back to the document but not return it from
        # this method
        rangesToIgnore.push(r) if normedRange is null

        normedRange

      # BrowserRange#normalize() modifies the DOM structure and deselects the
      # underlying text as a result. So here we remove the selected ranges and
      # reapply the new ones.
      selection.removeAllRanges()

    for r in rangesToIgnore
      selection.addRange(r)

    # Remove any ranges that fell outside of @wrapper.
    $.grep ranges, (range) ->
      # Add the normed range back to the selection if it exists.
      selection.addRange(range.toRange()) if range
      range

  # Public: Gets the target identified by the given NormalizedRange.
  #
  #
  # Returns an Object containing a `source` property and a `selector` Array.
  getTargetFromRange: (range) ->
    source: this.getHref()
    selector: [
      this.getRangeSelector range
      this.getTextQuoteSelector range
      this.getTextPositionSelector range
    ]

  # Public: Creates and returns a new annotation object. Publishes the
  # 'beforeAnnotationCreated' event to allow the new annotation to be modified.
  #
  # Examples
  #
  #   annotator.createAnnotation() # Returns {}
  #
  #   annotator.on 'beforeAnnotationCreated', (annotation) ->
  #     annotation.myProperty = 'This is a custom property'
  #   annotator.createAnnotation() # Returns {myProperty: "This is a…"}
  #
  # Returns a newly created annotation Object.
  createAnnotation: () ->
    annotation = {}
    this.publish('beforeAnnotationCreated', [annotation])
    annotation

  # Do some normalization to get a "canonical" form of a string.
  # Used to even out some browser differences.
  normalizeString: (string) -> string.replace /\s{2,}/g, " "

  # Find the given type of selector from an array of selectors, if it exists.
  # If it does not exist, null is returned.
  findSelector: (selectors, type) ->
    for selector in selectors
      if selector.type is type then return selector
    null

  # Try to determine the anchor position for a target
  # using the saved Range selector. The quote is verified.
  findAnchorFromRangeSelector: (target) ->
    selector = this.findSelector target.selector, "RangeSelector"
    unless selector? then return null

    # Try to apply the saved XPath
    normalizedRange = Range.sniff(selector).normalize @wrapper[0]
    # Look up the saved quote
    savedQuote = this.getQuoteForTarget target
    if savedQuote?
      # We have a saved quote, let's compare it to current content
      startInfo = @domMapper.getInfoForNode normalizedRange.start
      startOffset = startInfo.start
      endInfo = @domMapper.getInfoForNode normalizedRange.end
      endOffset = endInfo.end
      content = @domMapper.getContentForCharRange startOffset, endOffset
      currentQuote = this.normalizeString content
      if currentQuote isnt savedQuote
        console.log "Could not apply XPath selector to current document \
          because the quote has changed. (Saved quote is '#{savedQuote}'. \
          Current quote is '#{currentQuote}'.)"
        return null
      else
#        console.log "Saved quote matches."
    else
      console.log "No saved quote, nothing to compare. Assume that it's OK."
    range: normalizedRange
    quote: savedQuote

  # Try to determine the anchor position for a target
  # using the saved position selector. The quote is verified.
  findAnchorFromPositionSelector: (target) ->
    selector = this.findSelector target.selector, "TextPositionSelector"
    unless selector? then return null
    savedQuote = this.getQuoteForTarget target
    if savedQuote?
      # We have a saved quote, let's compare it to current content
      content = @domMapper.getContentForCharRange selector.start, selector.end
      currentQuote = this.normalizeString content
      if currentQuote isnt savedQuote
        console.log "Could not apply position selector" +
          " [#{selector.start}:#{selector.end}] to current document," +
          " because the quote has changed." +
          "(Saved quote is '#{savedQuote}'." +
          " Current quote is '#{currentQuote}'.)"
        return null
      else
#        console.log "Saved quote matches."
    else
      console.log "No saved quote, nothing to compare. Assume that it's okay."

    # OK, we have everything. Create a range from this.
    mappings = this.domMapper.getMappingsForCharRange selector.start,
        selector.end
    browserRange = new Range.BrowserRange mappings.realRange
    normalizedRange = browserRange.normalize @wrapper[0]
    range: normalizedRange
    quote: savedQuote

  findAnchorWithTwoPhaseFuzzyMatching: (target) ->
    # Fetch the quote and the context
    quoteSelector = this.findSelector target.selector, "TextQuoteSelector"
    prefix = quoteSelector?.prefix
    suffix = quoteSelector?.suffix
    quote = quoteSelector?.exact

    # No context, to joy
    unless (prefix? and suffix?) then return null

    # Fetch the expected start and end positions
    posSelector = this.findSelector target.selector, "TextPositionSelector"
    expectedStart = posSelector?.start
    expectedEnd = posSelector?.end

    options =
      contextMatchDistance: @domMapper.getDocLength() * 2
      contextMatchThreshold: 0.5
      patternMatchThreshold: 0.5
      flexContext: true
    result = @domMatcher.searchFuzzyWithContext prefix, suffix, quote,
      expectedStart, expectedEnd, false, null, options

    # If we did not got a result, give up
    unless result.matches.length
      console.log "Fuzzy matching did not return any results. Giving up on two-phase strategy."
      return null

    # here is our result
    match = result.matches[0]
    console.log "2-phase fuzzy found match:"
    console.log match

    # convert it to a Range
    browserRange = new Range.BrowserRange match.realRange
    normalizedRange = browserRange.normalize @wrapper[0]

    # return the anchor
    anchor =
      range: normalizedRange
      quote: unless match.exact then match.found
      diffHTML: unless match.exact then match.comparison.diffHTML
      diffCaseOnly: unless match.exact then match.exactExceptCase

    anchor

  findAnchorWithFuzzyMatching: (target) ->
    # Fetch the quote
    quoteSelector = this.findSelector target.selector, "TextQuoteSelector"
    quote = quoteSelector?.exact

    # No quote, no joy
    unless quote? then return null

    # For too short quotes, this strategy is bound to return false positives.
    # See https://github.com/hypothesis/h/issues/853 for details.
    return unless quote.length >= 32

    # Get a starting position for the search
    posSelector = this.findSelector target.selector, "TextPositionSelector"
    expectedStart = posSelector?.start

    # Get full document length
    len = this.domMapper.getDocLength()

    # If we don't have the position saved, start at the middle of the doc
    expectedStart ?= len / 2

    # Do the fuzzy search
    options =
      matchDistance: len * 2
      withFuzzyComparison: true
    result = @domMatcher.searchFuzzy quote, expectedStart, false, null, options

    # If we did not got a result, give up
    unless result.matches.length
      console.log "Fuzzy matching did not return any results. Giving up on one-phase strategy."
      return null

    # here is our result
    match = result.matches[0]
    console.log "1-phase fuzzy found match:"
    console.log match

    # convert it to a Range
    browserRange = new Range.BrowserRange match.realRange
    normalizedRange = browserRange.normalize @wrapper[0]

    # return the anchor
    anchor =
      range: normalizedRange
      quote: unless match.exact then match.found
      diffHTML: unless match.exact then match.comparison.diffHTML
      diffCaseOnly: unless match.exact then match.exactExceptCase

    anchor

  # Try to find the right anchoring point for a given target
  #
  # Returns a normalized range if succeeded, null otherwise
  findAnchor: (target) ->
    unless target?
      throw new Error "Trying to find anchor for null target!"
#    console.log "Trying to find anchor for target: "
#    console.log target

    strategies = [
      # Simple strategy based on DOM Range
      this.findAnchorFromRangeSelector

      # Position-based strategy. (The quote is verified.)
      # This can handle document structure changes,
      # but not the content changes.
      this.findAnchorFromPositionSelector

      # Two-phased fuzzy text matching strategy. (Using context and quote.)
      # This can handle document structure changes,
      # and also content changes.
      this.findAnchorWithTwoPhaseFuzzyMatching

      # Naive fuzzy text matching strategy. (Using only the quote.)
      # This can handle document structure changes,
      # and also content changes.
      this.findAnchorWithFuzzyMatching
    ]

    error = null
    anchor = null
    for fn in strategies
      try
        anchor ?= fn.call this, target
      catch error
        unless error instanceof Range.RangeError
          throw error
    {error, anchor}

  # Public: Initialises an annotation either from an object representation or
  # an annotation created with Annotator#createAnnotation(). It finds the
  # selected range and higlights the selection in the DOM, extracts the
  # quoted text and serializes the range.
  #
  # annotation - An annotation Object to initialise.
  #
  # Examples
  #
  #   # Create a brand new annotation from the currently selected text.
  #   annotation = annotator.createAnnotation()
  #   annotation = annotator.setupAnnotation(annotation)
  #   # annotation has now been assigned the currently selected range
  #   # and a highlight appended to the DOM.
  #
  #   # Add an existing annotation that has been stored elsewere to the DOM.
  #   annotation = getStoredAnnotationWithSerializedRanges()
  #   annotation = annotator.setupAnnotation(annotation)
  #
  # Returns the initialised annotation.
  setupAnnotation: (annotation) ->
    root = @wrapper[0]
    ranges = annotation.ranges or @selectedRanges or []

    # Upgrade format from v1.2.6 and earlier
    if annotation.ranges? then delete annotation.ranges

    annotation.target or= (this.getTargetFromRange(r) for r in ranges)

    unless annotation.target?
      throw new Error "Can not run setupAnnotation(). No target or selection available."

    normedRanges     = []
    annotation.quote = []

    for t in annotation.target
      try
        {anchor, error} = this.findAnchor t
        if error instanceof Range.RangeError
          this.publish('rangeNormalizeFail', [annotation, error.range, error])
        if anchor?
          t.quote = anchor.quote or $.trim(anchor.range.text())
          t.diffHTML = anchor.diffHTML
          t.diffCaseOnly = anchor.diffCaseOnly
          normedRanges.push anchor.range
          annotation.quote.push t.quote
        else
          console.log "Could not find anchor target for annotation '" +
              annotation.id + "'."
      catch exception
        if exception.stack? then console.log exception.stack
        console.log exception.message
        console.log exception


    annotation.ranges     = []
    annotation.highlights = []

    for normed in normedRanges
      annotation.ranges.push normed.serialize(@wrapper[0], '.annotator-hl')
      $.merge annotation.highlights, this.highlightRange(normed)

    # Join all the quotes into one string.
    annotation.quote = annotation.quote.join(' / ')

    # Save the annotation data on each highlighter element.
    $(annotation.highlights).data('annotation', annotation)

    annotation

  # Public: Publishes the 'beforeAnnotationUpdated' and 'annotationUpdated'
  # events. Listeners wishing to modify an updated annotation should subscribe
  # to 'beforeAnnotationUpdated' while listeners storing annotations should
  # subscribe to 'annotationUpdated'.
  #
  # annotation - An annotation Object to update.
  #
  # Examples
  #
  #   annotation = {tags: 'apples oranges pears'}
  #   annotator.on 'beforeAnnotationUpdated', (annotation) ->
  #     # validate or modify a property.
  #     annotation.tags = annotation.tags.split(' ')
  #   annotator.updateAnnotation(annotation)
  #   # => Returns ["apples", "oranges", "pears"]
  #
  # Returns annotation Object.
  updateAnnotation: (annotation) ->
    this.publish('beforeAnnotationUpdated', [annotation])
    this.publish('annotationUpdated', [annotation])
    annotation

  # Public: Deletes the annotation by removing the highlight from the DOM.
  # Publishes the 'annotationDeleted' event on completion.
  #
  # annotation - An annotation Object to delete.
  #
  # Returns deleted annotation.
  deleteAnnotation: (annotation) ->
    if annotation.highlights?
      for h in annotation.highlights when h.parentNode?
        child = h.childNodes[0]
        $(h).replaceWith(h.childNodes)
        window.DomTextMapper.changed child.parentNode,
          "removed hilite (annotation deleted)"

    this.publish('annotationDeleted', [annotation])
    annotation

  # Public: Loads an Array of annotations into the @element. Breaks the task
  # into chunks of 10 annotations.
  #
  # annotations - An Array of annotation Objects.
  #
  # Examples
  #
  #   loadAnnotationsFromStore (annotations) ->
  #     annotator.loadAnnotations(annotations)
  #
  # Returns itself for chaining.
  loadAnnotations: (annotations=[]) ->
    loader = (annList=[]) =>
      now = annList.splice(0,10)

      for n in now
        this.setupAnnotation(n)

      # If there are more to do, do them after a 10ms break (for browser
      # responsiveness).
      if annList.length > 0
        setTimeout((-> loader(annList)), 10)
      else
        this.publish 'annotationsLoaded', [clone]

    clone = annotations.slice()
    loader(annotations) if annotations.length
    this

  # Public: Calls the Store#dumpAnnotations() method.
  #
  # Returns dumped annotations Array or false if Store is not loaded.
  dumpAnnotations: () ->
    if @plugins['Store']
      @plugins['Store'].dumpAnnotations()
    else
      console.warn(_t("Can't dump annotations without Store plugin."))
      return false

  # Public: Wraps the DOM Nodes within the provided range with a highlight
  # element of the specified class and returns the highlight Elements.
  #
  # normedRange - A NormalizedRange to be highlighted.
  # cssClass - A CSS class to use for the highlight (default: 'annotator-hl')
  #
  # Returns an array of highlight Elements.
  highlightRange: (normedRange, cssClass='annotator-hl') ->
    white = /^\s*$/

    hl = $("<span class='#{cssClass}'></span>")

    # Ignore text nodes that contain only whitespace characters. This prevents
    # spans being injected between elements that can only contain a restricted
    # subset of nodes such as table rows and lists. This does mean that there
    # may be the odd abandoned whitespace node in a paragraph that is skipped
    # but better than breaking table layouts.

    for node in normedRange.textNodes() when not white.test node.nodeValue
      r = $(node).wrapAll(hl).parent().show()[0]
      window.DomTextMapper.changed node, "created hilite"
      r

  # Public: highlight a list of ranges
  #
  # normedRanges - An array of NormalizedRanges to be highlighted.
  # cssClass - A CSS class to use for the highlight (default: 'annotator-hl')
  #
  # Returns an array of highlight Elements.
  highlightRanges: (normedRanges, cssClass='annotator-hl') ->
    highlights = []
    for r in normedRanges
      $.merge highlights, this.highlightRange(r, cssClass)
    highlights

  # Public: Registers a plugin with the Annotator. A plugin can only be
  # registered once. The plugin will be instantiated in the following order.
  #
  # 1. A new instance of the plugin will be created (providing the @element and
  #    options as params) then assigned to the @plugins registry.
  # 2. The current Annotator instance will be attached to the plugin.
  # 3. The Plugin#pluginInit() method will be called if it exists.
  #
  # name    - Plugin to instantiate. Must be in the Annotator.Plugins namespace.
  # options - Any options to be provided to the plugin constructor.
  #
  # Examples
  #
  #   annotator
  #     .addPlugin('Tags')
  #     .addPlugin('Store', {
  #       prefix: '/store'
  #     })
  #     .addPlugin('Permissions', {
  #       user: 'Bill'
  #     })
  #
  # Returns itself to allow chaining.
  addPlugin: (name, options) ->
    if @plugins[name]
      console.error _t("You cannot have more than one instance of any plugin.")
    else
      klass = Annotator.Plugin[name]
      if typeof klass is 'function'
        @plugins[name] = new klass(@element[0], options)
        @plugins[name].annotator = this
        @plugins[name].pluginInit?()
      else
        console.error _t("Could not load ") + name + _t(" plugin. Have you included the appropriate <script> tag?")
    this # allow chaining

  # Public: Loads the @editor with the provided annotation and updates its
  # position in the window.
  #
  # annotation - An annotation to load into the editor.
  # location   - Position to set the Editor in the form {top: y, left: x}
  #
  # Examples
  #
  #   annotator.showEditor({text: "my comment"}, {top: 34, left: 234})
  #
  # Returns itself to allow chaining.
  showEditor: (annotation, location) =>
    @editor.element.css(location)
    @editor.load(annotation)
    this.publish('annotationEditorShown', [@editor, annotation])
    this

  # Callback method called when the @editor fires the "hide" event. Itself
  # publishes the 'annotationEditorHidden' event and resets the @ignoreMouseup
  # property to allow listening to mouse events.
  #
  # Returns nothing.
  onEditorHide: =>
    this.publish('annotationEditorHidden', [@editor])
    @ignoreMouseup = false

  # Callback method called when the @editor fires the "save" event. Itself
  # publishes the 'annotationEditorSubmit' event and creates/updates the
  # edited annotation.
  #
  # Returns nothing.
  onEditorSubmit: (annotation) =>
    this.publish('annotationEditorSubmit', [@editor, annotation])

  # Public: Loads the @viewer with an Array of annotations and positions it
  # at the location provided. Calls the 'annotationViewerShown' event.
  #
  # annotation - An Array of annotations to load into the viewer.
  # location   - Position to set the Viewer in the form {top: y, left: x}
  #
  # Examples
  #
  #   annotator.showViewer(
  #    [{text: "my comment"}, {text: "my other comment"}],
  #    {top: 34, left: 234})
  #   )
  #
  # Returns itself to allow chaining.
  showViewer: (annotations, location) =>
    @viewer.element.css(location)
    @viewer.load(annotations)

    this.publish('annotationViewerShown', [@viewer, annotations])

  # Annotator#element event callback. Allows 250ms for mouse pointer to get from
  # annotation highlight to @viewer to manipulate annotations. If timer expires
  # the @viewer is hidden.
  #
  # Returns nothing.
  startViewerHideTimer: =>
    # Don't do this if timer has already been set by another annotation.
    if not @viewerHideTimer
      @viewerHideTimer = setTimeout @viewer.hide, 250

  # Viewer#element event callback. Clears the timer set by
  # Annotator#startViewerHideTimer() when the @viewer is moused over.
  #
  # Returns nothing.
  clearViewerHideTimer: () =>
    clearTimeout(@viewerHideTimer)
    @viewerHideTimer = false

  # Annotator#element callback. Sets the @mouseIsDown property used to
  # determine if a selection may have started to true. Also calls
  # Annotator#startViewerHideTimer() to hide the Annotator#viewer.
  #
  # event - A mousedown Event object.
  #
  # Returns nothing.
  checkForStartSelection: (event) =>
    unless event and this.isAnnotator(event.target)
      this.startViewerHideTimer()
    @mouseIsDown = true

  # Annotator#element callback. Checks to see if a selection has been made
  # on mouseup and if so displays the Annotator#adder. If @ignoreMouseup is
  # set will do nothing. Also resets the @mouseIsDown property.
  #
  # event - A mouseup Event object.
  #
  # Returns nothing.
  checkForEndSelection: (event) =>
    @mouseIsDown = false

    # This prevents the note image from jumping away on the mouseup
    # of a click on icon.
    if @ignoreMouseup
      return

    # Get the currently selected ranges.
    @selectedRanges = this.getSelectedRanges()

    for range in @selectedRanges
      container = range.commonAncestor
      if $(container).hasClass('annotator-hl')
        container = $(container).parents(':not([class^=annotator-hl])')[0]
      return if this.isAnnotator(container)

    if event and @selectedRanges.length
      this.onSuccessfulSelection event
    else
      this.onFailedSelection event

  onSuccessfulSelection: (event) ->
    @adder
      .css(util.mousePosition(event, @wrapper[0]))
      .show()

  onFailedSelection: (event) ->
    @adder.hide()


  # Public: Determines if the provided element is part of the annotator plugin.
  # Useful for ignoring mouse actions on the annotator elements.
  # NOTE: The @wrapper is not included in this check.
  #
  # element - An Element or TextNode to check.
  #
  # Examples
  #
  #   span = document.createElement('span')
  #   annotator.isAnnotator(span) # => Returns false
  #
  #   annotator.isAnnotator(annotator.viewer.element) # => Returns true
  #
  # Returns true if the element is a child of an annotator element.
  isAnnotator: (element) ->
    !!$(element).parents().andSelf().filter('[class^=annotator-]').not(@wrapper).length

  # Annotator#element callback. Displays viewer with all annotations
  # associated with highlight Elements under the cursor.
  #
  # event - A mouseover Event object.
  #
  # Returns nothing.
  onHighlightMouseover: (event) =>
    # Cancel any pending hiding of the viewer.
    this.clearViewerHideTimer()

    # Don't do anything if we're making a selection or
    # already displaying the viewer
    return false if @mouseIsDown or @viewer.isShown()

    annotations = $(event.target)
      .parents('.annotator-hl')
      .andSelf()
      .map -> return $(this).data("annotation")

    this.showViewer($.makeArray(annotations), util.mousePosition(event, @wrapper[0]))

  # Annotator#element callback. Sets @ignoreMouseup to true to prevent
  # the annotation selection events firing when the adder is clicked.
  #
  # event - A mousedown Event object
  #
  # Returns nothing.
  onAdderMousedown: (event) =>
    event?.preventDefault()
    @ignoreMouseup = true

  # Annotator#element callback. Displays the @editor in place of the @adder and
  # loads in a newly created annotation Object. The click event is used as well
  # as the mousedown so that we get the :active state on the @adder when clicked
  #
  # event - A mousedown Event object
  #
  # Returns nothing.
  onAdderClick: (event) =>
    event?.preventDefault()

    # Hide the adder
    position = @adder.position()
    @adder.hide()

    # Create a new annotation.
    annotation = this.createAnnotation()

    # Extract the quotation and serialize the ranges
    annotation = this.setupAnnotation(annotation)

    # Show a temporary highlight so the user can see what they selected
    $(annotation.highlights).addClass('annotator-hl-temporary')

    # Make the highlights permanent if the annotation is saved
    save = =>
      do cleanup
      $(annotation.highlights).removeClass('annotator-hl-temporary')
      # Fire annotationCreated events so that plugins can react to them
      this.publish('annotationCreated', [annotation])

    # Remove the highlights if the edit is cancelled
    cancel = =>
      do cleanup
      this.deleteAnnotation(annotation)

    # Don't leak handlers at the end
    cleanup = =>
      this.unsubscribe('annotationEditorHidden', cancel)
      this.unsubscribe('annotationEditorSubmit', save)

    # Subscribe to the editor events
    this.subscribe('annotationEditorHidden', cancel)
    this.subscribe('annotationEditorSubmit', save)

    # Display the editor.
    this.showEditor(annotation, position)

  # Annotator#viewer callback function. Displays the Annotator#editor in the
  # positions of the Annotator#viewer and loads the passed annotation for
  # editing.
  #
  # annotation - An annotation Object for editing.
  #
  # Returns nothing.
  onEditAnnotation: (annotation) =>
    offset = @viewer.element.position()

    # Update the annotation when the editor is saved
    update = =>
      do cleanup
      this.updateAnnotation(annotation)

    # Remove handlers when finished
    cleanup = =>
      this.unsubscribe('annotationEditorHidden', cleanup)
      this.unsubscribe('annotationEditorSubmit', update)

    # Subscribe to the editor events
    this.subscribe('annotationEditorHidden', cleanup)
    this.subscribe('annotationEditorSubmit', update)

    # Replace the viewer with the editor
    @viewer.hide()
    this.showEditor(annotation, offset)

  # Annotator#viewer callback function. Deletes the annotation provided to the
  # callback.
  #
  # annotation - An annotation Object for deletion.
  #
  # Returns nothing.
  onDeleteAnnotation: (annotation) =>
    @viewer.hide()

    # Delete highlight elements.
    this.deleteAnnotation annotation

# Create namespace for Annotator plugins
class Annotator.Plugin extends Delegator
  constructor: (element, options) ->
    super

  pluginInit: ->

# Sniff the browser environment and attempt to add missing functionality.
g = util.getGlobal()

if not g.document?.evaluate?
  $.getScript('http://assets.annotateit.org/vendor/xpath.min.js')

if not g.getSelection?
  $.getScript('http://assets.annotateit.org/vendor/ierange.min.js')

if not g.JSON?
  $.getScript('http://assets.annotateit.org/vendor/json2.min.js')

# Ensure the Node constants are defined
if not g.Node?
  g.Node =
    ELEMENT_NODE                :  1
    ATTRIBUTE_NODE              :  2
    TEXT_NODE                   :  3
    CDATA_SECTION_NODE          :  4
    ENTITY_REFERENCE_NODE       :  5
    ENTITY_NODE                 :  6
    PROCESSING_INSTRUCTION_NODE :  7
    COMMENT_NODE                :  8
    DOCUMENT_NODE               :  9
    DOCUMENT_TYPE_NODE          : 10
    DOCUMENT_FRAGMENT_NODE      : 11
    NOTATION_NODE               : 12

# Bind our local copy of jQuery so plugins can use the extensions.
Annotator.$ = $

# Export other modules for use in plugins.
Annotator.Delegator = Delegator
Annotator.Range = Range
Annotator.Util = Util

# Bind gettext helper so plugins can use localisation.
Annotator._t = _t

# Returns true if the Annotator can be used in the current browser.
Annotator.supported = -> (-> !!this.getSelection)()

# Restores the Annotator property on the global object to it's
# previous value and returns the Annotator.
Annotator.noConflict = ->
  util.getGlobal().Annotator = _Annotator
  this

# Create global access for Annotator
$.fn.annotator = (options) ->
  args = Array::slice.call(arguments, 1)
  this.each ->
    # check the data() cache, if it's there we'll call the method requested
    instance = $.data(this, 'annotator')
    if instance
      options && instance[options].apply(instance, args)
    else
      instance = new Annotator(this, options)
      $.data(this, 'annotator', instance)

# Export Annotator object.
this.Annotator = Annotator;
