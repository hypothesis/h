$ = Annotator.$

class Annotator.Guest extends Annotator
  # Events to be bound on Annotator#element.
  events:
    ".annotator-adder button click":     "onAdderClick"
    ".annotator-adder button mousedown": "onAdderMousedown"
    ".annotator-hl mousedown": "onHighlightMousedown"
    ".annotator-hl click": "onHighlightClick"
    "setTool": "onSetTool"
    "setVisibleHighlights": "onSetVisibleHighlights"

  # Plugin configuration
  options:
    Document: {}

  # Internal state
  comments: null
  tool: 'comment'
  visibleHighlights: false

  constructor: (element, options) ->
    Gettext.prototype.parse_locale_data annotator_locale_data

    options.noScan = true
    super
    delete @options.noScan

    # Create an array for holding the comments
    @comments = []

    @frame = $('<div></div>')
    .appendTo(@wrapper)
    .addClass('annotator-frame annotator-outer annotator-collapsed')

    delete @options.app

    this.addPlugin 'Bridge',
      formatter: (annotation) =>
        formatted = {}
        if annotation.document?
          formatted['uri'] = @plugins.Document.uri()
        for k, v of annotation when k isnt 'highlights'
          formatted[k] = v
        # Work around issue in jschannel where a repeated object is considered
        # recursive, even if it is not its own ancestor.
        if formatted.document?.title
          formatted.document.title = formatted.document.title.slice()
        formatted
      onConnect: (source, origin, scope) =>
        @panel = this._setupXDM
          window: source
          origin: origin
          scope: "#{scope}:provider"
          onReady: =>
            console.log "Guest functions are ready for #{origin}"
            event = document.createEvent "UIEvents"
            event.initUIEvent "annotatorReady", false, false, window, 0
            window.dispatchEvent event

    # Load plugins
    for own name, opts of @options
      if not @plugins[name]
        this.addPlugin(name, opts)

    # Scan the document text with the DOM Text libraries
    this.scanDocument "Annotator initialized"

    # Watch for deleted comments
    this.subscribe 'annotationDeleted', (annotation) =>
      if this.isComment annotation
        i = @comments.indexOf annotation
        if i isnt -1
          @comments[i..i] = []
          @plugins.Heatmap._update()

  _setupXDM: (options) ->
    # jschannel chokes FF and Chrome extension origins.
    if (options.origin.match /^chrome-extension:\/\//) or
        (options.origin.match /^resource:\/\//)
      options.origin = '*'

    channel = Channel.build options

    channel

    .bind('onEditorHide', this.onEditorHide)
    .bind('onEditorSubmit', this.onEditorSubmit)

    .bind('setDynamicBucketMode', (ctx, value) =>
      return unless @plugins.Heatmap
      @plugins.Heatmap.dynamicBucket = value
      if value then @plugins.Heatmap._update()
    )

    .bind('setActiveHighlights', (ctx, tags=[]) =>
      @wrapper.find('.annotator-hl')
      .each ->
        if $(this).data('annotation').$$tag in tags
          $(this).addClass('annotator-hl-active')
        else if not $(this).hasClass('annotator-hl-temporary')
          $(this).removeClass('annotator-hl-active')
    )

    .bind('scrollTo', (ctx, tag) =>
      @wrapper.find('.annotator-hl')
      .each ->
        if $(this).data('annotation').$$tag is tag
          $(this).scrollintoview()
    )

    .bind('adderClick', =>
      @onAdderClick @event
    )

    .bind('getDocumentInfo', =>
      return {
        uri: @plugins.Document.uri()
        metadata: @plugins.Document.metadata
      }
    )

    .bind('setTool', (ctx, name) =>
      this.setTool name
      this.publish 'setTool', name
    )

    .bind('setVisibleHighlights', (ctx, state) =>
      this.setVisibleHighlights state, false
      this.publish 'setVisibleHighlights', state
    )

    .bind('onLogin', (ctx, user) =>
      if @_pendingLogin?
        @_pendingLogin?.resolve()
        delete @_pendingLogin
      else
        event = document.createEvent "UIEvents"
        event.initUIEvent "annotatorLogin", false, false, window, 0
        event.user = user
        window.dispatchEvent event
    )

    .bind('onLoginFailed', (ctx, data) =>
      @_pendingLogin?.reject data
      delete @_pendingLogin
    )

    .bind('onLogout', =>
      if @_pendingLogout?
        @_pendingLogout.resolve()
        delete @_pendingLogout
      else
        event = document.createEvent "UIEvents"
        event.initUIEvent "annotatorLogout", false, false, window, 0
        window.dispatchEvent event
    )

  scanDocument: (reason = "something happened") =>
    try
      console.log "Analyzing host frame, because " + reason + "..."
      r = this._scan()
      scanTime = r.time
      console.log "Traversal+scan took " + scanTime + " ms."
    catch e
      console.log e.message
      console.log e.stack

  _setupWrapper: ->
    @wrapper = @element
    .on 'click', =>
      unless @ignoreMouseup or @noBack
        setTimeout =>
          unless @selectedRanges?.length
            @panel?.notify method: 'back'
    this._setupMatching()
    @domMatcher.setRootNode @wrapper[0]
    this

  # These methods aren't used in the iframe-hosted configuration of Annotator.
  _setupViewer: -> this
  _setupEditor: -> this

  showViewer: (annotations) =>
    @panel?.notify method: "showViewer", params: (a.id for a in annotations)

  updateViewer: (annotations) =>
    @panel?.notify method: "updateViewer", params: (a.id for a in annotations)

  showEditor: (annotation) => @plugins.Bridge.showEditor annotation

  checkForStartSelection: (event) =>
    # Override to prevent Annotator choking when this ties to access the
    # viewer but preserve the manipulation of the attribute `mouseIsDown` which
    # is needed for preventing the panel from closing while annotating.
    unless event and this.isAnnotator(event.target)
      @mouseIsDown = true

  confirmSelection: ->
    return true unless @selectedRanges.length is 1

    target = this.getTargetFromRange @selectedRanges[0]
    selector = this.findSelector target.selector, "TextQuoteSelector"
    length = selector.exact.length

    if length > 2 then return true

    return confirm "You have selected a very short piece of text: only " + length + " chars. Are you sure you want to highlight this?"

  onSuccessfulSelection: (event) ->
    if @tool is 'highlight'

      # Do we really want to make this selection?
      return unless this.confirmSelection()

      # Create the annotation right away

      # Don't use the default method to create an annotation,
      # because we don't want to publish the beforeAnnotationCreated event
      # just yet.
      #
      # annotation = this.createAnnotation()
      #
      # Create an empty annotation manually instead
      annotation = {inject: true}

      annotation = this.setupAnnotation annotation
      $(annotation.highlights).addClass 'annotator-hl'

      # Notify listeners
      this.publish 'beforeAnnotationCreated', annotation
      this.publish 'annotationCreated', annotation
    else
      super event

  # When clicking on a highlight in highlighting mode,
  # set @noBack to true to prevent the sidebar from closing
  onHighlightMousedown: (event) =>
    if (@tool is 'highlight') or @visibleHighlights then @noBack = true

  # When clicking on a highlight in highlighting mode,
  # tell the sidebar to bring up the viewer for the relevant annotations
  onHighlightClick: (event) =>
    return unless (@tool is 'highlight') or @visibleHighlights and @noBack

    # Collect relevant annotations
    annotations = $(event.target)
      .parents('.annotator-hl')
      .addBack()
      .map -> return $(this).data("annotation")

    # Tell sidebar to show the viewer for these annotations
    this.showViewer annotations

    # We have already prevented closing the sidebar, now reset this flag
    @noBack = false

  setTool: (name) ->
    @tool = name
    @panel?.notify
      method: 'setTool'
      params: name

  setVisibleHighlights: (state=true, notify=true) ->
    if notify
      @panel?.notify
        method: 'setVisibleHighlights'
        params: state
    else
      markerClass = 'annotator-highlights-always-on'
      if state or this.tool is 'highlight'
        @element.addClass markerClass
      else
        @element.removeClass markerClass

  addComment: ->
    sel = @selectedRanges   # Save the selection
    # Nuke the selection, since we won't be using that.
    # We will attach this to the end of the document.
    # Our override for setupAnnotation will add that highlight.
    @selectedRanges = []
    this.onAdderClick()     # Open editor (with 0 targets)
    @selectedRanges = sel # restore the selection

  # Is this annotation a comment?
  isComment: (annotation) ->
    # No targets and no references means that this is a comment.    
    not (annotation.inject or annotation.references?.length or annotation.target?.length)

  # Override for setupAnnotation, to handle comments
  setupAnnotation: (annotation) ->
    annotation = super # Set up annotation as usual
    if this.isComment annotation then @comments.push annotation
    annotation

  # Open the sidebar
  showFrame: ->
    @panel?.notify method: 'open'

  # Close the sidebar
  hideFrame: ->
    @panel?.notify method: 'back'

  addToken: (token) =>
    @api.notify
      method: 'addToken'
      params: token

  onAdderClick: (event) =>
    """
    Differs from upstream in a few ways:
    - Don't fire annotationCreated events: that's the job of the sidebar
    - Save the event for retriggering if login interrupts the flow
    """
    event?.preventDefault()

    # Save the event for restarting edit
    @event = event

    # Hide the adder
    @adder.hide()
    position = @adder.position()

    # Show a temporary highlight so the user can see what they selected
    # Also extract the quotation and serialize the ranges
    annotation = this.setupAnnotation(this.createAnnotation())
    $(annotation.highlights).addClass('annotator-hl-temporary')

    # Subscribe to the editor events

    # Make the highlights permanent if the annotation is saved
    save = =>
      do cleanup
      $(annotation.highlights).removeClass('annotator-hl-temporary')

    # Remove the highlights if the edit is cancelled
    cancel = =>
      do cleanup
      this.deleteAnnotation(annotation)

    # Don't leak handlers at the end
    cleanup = =>
      this.unsubscribe('annotationEditorHidden', cancel)
      this.unsubscribe('annotationEditorSubmit', save)

    this.subscribe('annotationEditorHidden', cancel)
    this.subscribe('annotationEditorSubmit', save)

    # Display the editor.
    this.showEditor(annotation, position)

  onSetTool: (name) ->
    switch name
      when 'comment'
        this.setVisibleHighlights this.visibleHighlights, false
      when 'highlight'
        this.setVisibleHighlights true, false

  onSetVisibleHighlights: (state) =>
    this.visibleHighlights = state
    this.setVisibleHighlights state, false

  # TODO: Workaround for double annotation deletion.
  # The short story: hiding the editor sometimes triggers
  # a spurious annotation delete.
  # Uncomment the traces below to investigate this further.
  deleteAnnotation: (annotation) ->
    if annotation.deleted
#      console.log "Not deleting annotation the second time."
#      console.trace()
      return
    else
#      console.log "Deleting an annotation in " + @role + "."
#      console.trace()
      annotation.deleted = true
    super

  # Public API to trigger a login
  loginWithUsernameAndPassword: (username, password) ->
    @_pendingLogin = @constructor.$.Deferred()
    if @panel?
      @panel.notify method: "login", params:
        username: username
        password: password
    else
      @panel.reject "Panel connection is not yet available."
    @_pendingLogin

  # Public API to trigger a logout
  logout: ->
    @_pendingLogout = @constructor.$.Deferred()
    if @panel?
      @panel.notify method: "logout"
    else
      @pendingLogout.reject "Panel connection is not yet available."
    @_pendingLogout

  # Public API to get login status
  getLoginStatus: ->
    result = @constructor.$.Deferred()
    if @panel?
      @panel.call
       method: "getLoginStatus"
       success: (data) -> result.resolve data
       error: (problem) -> result.reject problem
    else
      result.reject "Panel connection is not yet available."
    result