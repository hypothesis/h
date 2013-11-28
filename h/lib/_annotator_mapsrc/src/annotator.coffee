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

# Fake two-phase / pagination support, used for HTML documents
class DummyDocumentAccess

  @applicable: -> true
  getPageIndex: -> 0
  getPageCount: -> 1
  getPageIndexForPos: -> 0
  isPageMapped: -> true
  scan: ->

class Annotator extends Delegator
  # Events to be bound on Annotator#element.
  events:
    ".annotator-adder button click":     "onAdderClick"
    ".annotator-adder button mousedown": "onAdderMousedown"

  html:
    adder:   '<div class="annotator-adder"><button>' + _t('Annotate') + '</button></div>'
    wrapper: '<div class="annotator-wrapper"></div>'

  options: # Configuration options
    readOnly: false # Start Annotator in read-only mode. No controls will be shown.

  plugins: {}

  editor: null

  viewer: null

  selectedTargets: null

  mouseIsDown: false

  inAdderClick: false

  canAnnotate: false

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
    @anchoringStrategies = []

    # Return early if the annotator is not supported.
    return this unless Annotator.supported()
    this._setupDocumentEvents() unless @options.readOnly
    this._setupAnchorEvents()
    this._setupWrapper()
    this._setupDocumentAccessStrategies()
    this._setupViewer()._setupEditor()
    this._setupDynamicStyle()

    # Perform initial DOM scan, unless told not to.
    this._scan() unless @options.noScan

    # Create adder
    this.adder = $(this.html.adder).appendTo(@wrapper).hide()

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
  _chooseAccessPolicy: ->
    if @domMapper? then return

    # Go over the available strategies
    for s in @documentAccessStrategies
      # Can we use this strategy for this document?
      if s.mapper.applicable()
        @documentAccessStrategy = s
        console.log "Selected document access strategy: " + s.name
        @domMapper = new s.mapper()
        @anchors = {}
        addEventListener "docPageMapped", (evt) =>
          @_realizePage evt.pageIndex
        addEventListener "docPageUnmapped", (evt) =>
          @_virtualizePage evt.pageIndex
        s.init?()
        return this

  # Perform a scan of the DOM. Required for finding anchors.
  _scan: ->
    # If we haven't yet chosen a document access strategy, do so now.
    this._chooseAccessPolicy() unless @domMapper
    @pendingScan = @domMapper.scan()
    if @pendingScan?
      console.log "Waiting for scan to end, then enabling annotating"
      @pendingScan.then => @enableAnnotating()
    else
      console.log "Scan finished, enabling annotating"
      @enableAnnotating()

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
      "mousedown": this.checkForStartSelection
    })
    this

  # Sets up handlers to anchor-related events
  _setupAnchorEvents: ->
    # When annotations are updated
    @on 'annotationUpdated', (annotation) =>
      # Notify the anchors
      for anchor in annotation.anchors or []
        anchor.annotationUpdated()

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

  # Enables or disables the creation of annotations
  #
  # When it's set to false, nobody os supposed to call
  # onSuccessfulSelection()
  enableAnnotating: (value = true, local = true) ->
    # If we already have this setting, do nothing
    return if value is @canAnnotate

    # Set the field
    @canAnnotate = value

    # Publish an event, so that others can react
    this.publish "enableAnnotating", value

    # If this call came from "outside" (whatever it means), and annotation
    # is now disabled, then hide the adder.
    @adder.hide() unless value or local

  # Shortcut to disable annotating
  disableAnnotating: (local = true) -> this.enableAnnotating false, local

  # Utility function to get the decoded form of the document URI
  getHref: =>
    uri = decodeURIComponent document.location.href
    if document.location.hash then uri = uri.slice 0, (-1 * location.hash.length)
    $('meta[property^="og:url"]').each -> uri = decodeURIComponent this.content
    $('link[rel^="canonical"]').each -> uri = decodeURIComponent this.href
    return uri

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

  # Try to find the right anchoring point for a given target
  #
  # Returns an Anchor object if succeeded, null otherwise
  createAnchor: (annotation, target) ->
    unless target?
      throw new Error "Trying to find anchor for null target!"
#    console.log "Trying to find anchor for target: "
#    console.log target

    error = null
    anchor = null
    for s in @anchoringStrategies
      try
        a = s.code.call this, annotation, target
        if a
#          console.log "Strategy '" + s.name + "' yielded an anchor."
          return result: a
#        else
#          console.log "Strategy '" + s.name + "' did NOT yield an anchor."
      catch error
#        console.log "Strategy '" + s.name + "' has thrown an error."
        if error instanceof Range.RangeError
          return error: error
        else
          throw error

    return error: "No strategies worked."

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
    # If this is a new annotation, we might have to add the targets
    annotation.target ?= @selectedTargets
    @selectedTargets = []

    unless annotation.target?
      throw new Error "Can not run setupAnnotation(). No target or selection available."

    annotation.quote = []
    annotation.anchors = []

    for t in annotation.target
      try
        # Create an anchor for this target
        result = this.createAnchor annotation, t
        anchor = result.result
        if result.error? instanceof Range.RangeError
          this.publish 'rangeNormalizeFail', [annotation, result.error.range, result.error]
        if anchor?
          annotation.quote.push t.quote = anchor.quote
          t.diffHTML = anchor.diffHTML
          t.diffCaseOnly = anchor.diffCaseOnly

          # Store this anchor for the annotation
          annotation.anchors.push anchor

          # Store the anchor for all involved pages
          for pageIndex in [anchor.startPage .. anchor.endPage]
            @anchors[pageIndex] ?= []
            @anchors[pageIndex].push anchor

          # Realizing the anchor
          anchor.realize()

        else
          console.log "Could not create anchor for annotation '",
            annotation.id, "'."
      catch exception
        if exception.stack? then console.log exception.stack
        console.log exception.message
        console.log exception

    # Join all the quotes into one string.
    annotation.quote = annotation.quote.join(' / ')

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
    if annotation.anchors?    
      for a in annotation.anchors
        a.remove()

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

    if annotations.length # Do we have to do something?
      # Do we have a doc access strategy? If we don't have it yet, scan!
      @_scan() unless @domMapper
      if @pendingScan?    # Is there a pending scan?
        # Schedule the parsing the annotations for
        # when scan has finished
        @pendingScan.then =>
          #console.log "Document scan finished. Can start anchoring."
          setTimeout => loader annotations
      else # no pending scan
        # We can start parsing them right away
        loader annotations
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
  # publishes the 'annotationEditorHidden' event and sets the @canAnnotate
  # property to allow the creation of new annotations
  #
  # Returns nothing.
  onEditorHide: =>
    this.publish('annotationEditorHidden', [@editor])
    this.enableAnnotating()

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

  # This method is to be called by the mechanisms responsible for
  # triggering annotation (and highlight) creation.
  #
  # event - any event which has triggered this.
  #         The following fields are used:
  #   targets: an array of targets, which should be used to anchor the
  #            newly created annotation
  #   pageX and pageY: if the adder button is shown, use there coordinates
  #
  # immadiate - should we show the adder button, or should be proceed
  #             to create the annotation/highlight immediately ?
  #
  # returns false if the creation of annotations is forbidden at the moment,
  # true otherwise.
  onSuccessfulSelection: (event, immediate = false) ->
    # Check whether we got a proper event
    unless event?
      throw "Called onSuccessfulSelection without an event!"
    unless event.targets?
      throw "Called onSuccessulSelection with an event with missing targets!"

    # Are we allowed to create annotations?
    unless @canAnnotate
      #@Annotator.showNotification "You are already editing an annotation!",
      #  @Annotator.Notification.INFO
      return false

    # Store the selected targets
    @selectedTargets = event.targets

    # Do we want immediate annotation?
    if immediate
      # Create an annotation
      @onAdderClick event
    else
      # Show the adder button
      @adder
        .css(util.mousePosition(event, @wrapper[0]))
        .show()

    true

  onFailedSelection: (event) ->
    @adder.hide()
    @selectedTargets = []


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

  # Annotator#element callback. Sets the @canAnnotate to false to prevent
  # the annotation selection events firing when the adder is clicked.
  #
  # event - A mousedown Event object
  #
  # Returns nothing.
  onAdderMousedown: (event) =>
    event?.preventDefault()
    this.disableAnnotating()
    @inAdderClick = true

  # Annotator#element callback. Displays the @editor in place of the @adder and
  # loads in a newly created annotation Object. The click event is used as well
  # as the mousedown so that we get the :active state on the @adder when clicked
  #
  # event - A mousedown Event object
  #
  # Returns nothing.
  onAdderClick: (event) =>
    event?.preventDefault?()

    # Hide the adder
    position = @adder.position()
    @adder.hide()
    @inAdderClick = false

    # Create a new annotation.
    annotation = this.createAnnotation()

    # Extract the quotation and serialize the ranges
    annotation = this.setupAnnotation(annotation)

    # Show a temporary highlight so the user can see what they selected
    for anchor in annotation.anchors
      for page, hl of anchor.highlight
        hl.setTemporary true

    # Make the highlights permanent if the annotation is saved
    save = =>
      do cleanup
      for anchor in annotation.anchors
        for page, hl of anchor.highlight
          hl.setTemporary false
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

  # Collect all the highlights (optionally for a given set of annotations)
  getHighlights: (annotations) ->
    results = []
    if annotations?
      # Collect only the given set of annotations
      for annotation in annotations
        for anchor in annotation.anchors
          for page, hl of anchor.highlight
            results.push hl
    else
      # Collect from everywhere
      for page, anchors of @anchors
        $.merge results, (anchor.highlight[page] for anchor in anchors when anchor.highlight[page]?)
    results

  # Realize anchors on a given pages
  _realizePage: (index) ->
    # If the page is not mapped, give up
    return unless @domMapper.isPageMapped index

    # Go over all anchors related to this page
    for anchor in @anchors[index] ? []
      anchor.realize()

  # Virtualize anchors on a given page
  _virtualizePage: (index) ->
    # Go over all anchors related to this page
    for anchor in @anchors[index] ? []
      anchor.virtualize index

  onAnchorMouseover: (annotations, highlightType) ->
    #console.log "Mouse over annotations:", annotations

    # Cancel any pending hiding of the viewer.
    this.clearViewerHideTimer()

    # Don't do anything if we're making a selection or
    # already displaying the viewer
    return false if @mouseIsDown or @viewer.isShown()

    this.showViewer(annotations, util.mousePosition(event, @wrapper[0]))

  onAnchorMouseout: (annotations, highlightType) ->
    #console.log "Mouse out on annotations:", annotations
    this.startViewerHideTimer()

  onAnchorMousedown: (annotations, highlightType) ->
    #console.log "Mouse down on annotations:", annotations

  onAnchorClick: (annotations, highlightType) ->
    #console.log "Click on annotations:", annotations

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
Annotator.util = util
Annotator.Util = Util

Annotator.Highlight = Highlight
Annotator.Anchor = Anchor

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
