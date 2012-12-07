class Hypothesis extends Annotator
  # Events - overridden for good measure. Unused in the angular Annotator.
  events: {}

  # Plugin configuration
  options:
    Heatmap: {}
    HypothesisPermissions:
      showEditPermissionsCheckbox: false,
      showViewPermissionsCheckbox: false,
      userString: (user) -> user.replace(/^acct:(.+)@(.+)$/, '$1 on $2')

  # Internal state
  detail: false      # * Whether the viewer shows a summary or detail listing
  hash: -1           # * cheap UUID :cake:
  cache: null        # * Annotation cache
  visible: false     # * Whether the sidebar is visible
  unsaved_drafts: [] # * Unsaved drafts currenty open

  this.$inject = ['$cacheFactory', '$document', '$location', '$rootScope']
  constructor: ($cacheFactory, $document, $location, $rootScope) ->
    super $document

    @cache = $cacheFactory 'annotations'

    # Load plugins
    for own name, opts of @options
      if not @plugins[name] and name of Annotator.Plugin
        this.addPlugin(name, opts)

    # Establish cross-domain communication to the widget host
    @provider = new easyXDM.Rpc
      swf: @options.swf
      onReady: this._initialize
    ,
      local:
        publish: (event, args, k, fk) =>
          if event in ['annotationCreated']
            [h] = args
            annotation = @cache[h]
            this.publish event, [annotation]
        addPlugin: => this.addPlugin arguments...
        createAnnotation: =>
          if @plugins.HypothesisPermissions.user?
            @cache[h = ++@hash] = this.createAnnotation()
            h
          else
            this.showAuth true
            this.show()
            null
        showEditor: (stub) =>
          return unless this._canCloseUnsaved()
          h = stub.hash
          annotation = $.extend @cache[h], stub,
            hash:
              toJSON: => undefined
              valueOf: => h
          this.showEditor annotation
        # This guy does stuff when you "back out" of the interface.
        # (Currently triggered by a click on the source page.)
        back: =>
          if $location.path() == '/viewer' and $location.search()?.detail?
            $rootScope.$apply => $location.search('detail', null).replace()
          else
            this.hide()
        update: => this.publish 'hostUpdated'
      remote:
        publish: {}
        setupAnnotation: {}
        onEditorHide: {}
        onEditorSubmit: {}
        showFrame: {}
        hideFrame: {}
        dragFrame: {}
        getHighlights: {}
        setActiveHighlights: {}
        getMaxBottom: {}
        scrollTop: {}

  _initialize: =>
    @provider.getMaxBottom (max) =>
      @element.find('#toolbar').css("top", "#{max}px")
      @element.find('#gutter').css("margin-top", "#{max}px")
      @plugins.Heatmap.BUCKET_THRESHOLD_PAD += max

    this.subscribe 'beforeAnnotationCreated', (annotation) =>
      annotation.created = annotation.updated = (new Date()).toString()
      annotation.user = @plugins.HypothesisPermissions.options.userId(
        @plugins.HypothesisPermissions.user)

    this.publish 'hostUpdated'

  _setupWrapper: ->
    @wrapper = @element.find('#wrapper')
    .on 'mousewheel', (event, delta) ->
      # prevent overscroll from scrolling host frame
      # This is actually a bit tricky. Starting from the event target and
      # working up the DOM tree, find an element which is scrollable
      # and has a scrollHeight larger than its clientHeight.
      # I've obsered that some styles, such as :before content, may increase
      # scrollHeight of non-scrollable elements, and that there a mysterious
      # discrepancy of 1px sometimes occurs that invalidates the equation
      # typically cited for determining when scrolling has reached bottom:
      #   (scrollHeight - scrollTop == clientHeight)
      $current = $(event.target)
      while (
        ($current.css('overflow') in ['visible', '']) or
        ($current[0].scrollHeight == $current[0].clientHeight)
      )
        $current = $current.parent()
        if not $current[0]? then return event.preventDefault()
      scrollTop = $current[0].scrollTop
      scrollEnd = $current[0].scrollHeight - $current[0].clientHeight
      if delta > 0 and scrollTop == 0
        event.preventDefault()
      else if delta < 0 and scrollEnd - scrollTop <= 1
        event.preventDefault()
    this

  _setupDocumentEvents: ->
    el = document.createElementNS 'http://www.w3.org/1999/xhtml', 'canvas'
    el.width = el.height = 1
    @element.find('body').append el

    handle = @element.find('#toolbar .tri')[0]
    handle.addEventListener 'dragstart', (event) =>
      event.dataTransfer.setData 'text/plain', ''
      event.dataTransfer.setDragImage el, 0, 0
      @provider.dragFrame event.screenX
    handle.addEventListener 'dragend', (event) =>
      @provider.dragFrame event.screenX
    @element[0].addEventListener 'dragover', (event) =>
      @provider.dragFrame event.screenX
    @element[0].addEventListener 'dragleave', (event) =>
      @provider.dragFrame event.screenX

    this

  _setupDynamicStyle: ->
    this

  _setupViewer: ->
    # Not used in the angular version.
    this

  # Creates an instance of the Annotator.Editor and assigns it to @editor.
  # Appends this to the @wrapper and sets up event listeners.
  #
  # Returns itself for chaining.
  _setupEditor: ->
    @editor = this._createEditor()
    .on 'hide save', =>
      if @unsaved_drafts.indexOf(@editor) > -1
        @unsaved_drafts.splice(@unsaved_drafts.indexOf(@editor), 1)
    .on 'hide', =>
      @provider.onEditorHide()
    .on 'save', =>
      @provider.onEditorSubmit()
    this

  _createEditor: ->
    editor = new Annotator.Editor()
    editor.hide()
    editor.fields = [{
      element: editor.element,
      load: (field, annotation) ->
        $(field).find('textarea').val(annotation.text || '')
      submit: (field, annotation) ->
        annotation.text = $(field).find('textarea').val()
    }]

    @unsaved_drafts.push editor
    editor

  # Public: Initialises an annotation either from an object representation or
  # an annotation created with Annotator#createAnnotation(). It finds the
  # selected range and higlights the selection in the DOM.
  #
  # annotation - An annotation Object to initialise.
  # fireEvents - Will fire the 'annotationCreated' event if true.
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
    # Delagate to Annotator implementation after we give it a valid array of
    # ranges. This is needed until Annotator stops assuming ranges need to be
    # added.
    if annotation.thread
      annotation.ranges = []

    if not annotation.hash
      @cache[h = ++@hash] = $.extend annotation,
        hash:
          toJSON: => undefined
          valueOf: => h
    stub =
      hash: annotation.hash.valueOf()
      ranges: annotation.ranges
    @provider.setupAnnotation stub

  showViewer: (annotations=[], detail=false) =>
    if (@visible and not detail) or @unsaved_drafts.indexOf(@editor) > -1
      if not this._canCloseUnsaved() then return

    # Not implemented

  showEditor: (annotation) =>
    @editor.load(annotation)
    @editor.element.find('.annotator-controls').remove()

    quote = annotation.quote.replace(/\u00a0/g, ' ') # replace &nbsp;
    excerpt = $('<li class="paper excerpt">')
    excerpt.append($("<blockquote>#{quote}</blockquote>"))

    item = $('<li class="annotation paper writer">')
    item.append($(Handlebars.templates.editor(annotation)))

    @editor.element.find('.annotator-listing').empty()
      .append(excerpt)
      .append(item)
      .find(":input:first").focus()

    @unsaved_drafts.push @editor
    this.show()

  show: =>
    @visible = true
    @provider.showFrame()
    @element.find('#toolbar').addClass('shown')
      .find('.tri').attr('draggable', true)

  hide: =>
    @lastWidth = window.innerWidth
    @visible = false
    @provider.setActiveHighlights []
    @provider.hideFrame()
    @element.find('#toolbar').removeClass('shown')
      .find('.tri').attr('draggable', false)

  _canCloseUnsaved: ->
    # See if there's an unsaved/uncancelled reply
    can_close = true
    open_editors = 0
    for editor in @unsaved_drafts
      unsaved_text = editor.element.find(':input:first').attr 'value'
      if unsaved_text? and unsaved_text.toString().length > 0
        open_editors += 1

    if open_editors > 0
      if open_editors > 1
        ctext = "You have #{open_editors} unsaved replies."
      else
        ctext = "You have an unsaved reply."
      ctext = ctext + " Do you really want to close the view?"
      can_close = confirm ctext

    if can_close then @unsaved_drafts = []
    can_close

  threadId: (annotation) ->
    if annotation?.thread?
      annotation.thread + '/' + annotation.id
    else
      annotation.id


angular.module('h.services', [])
  .service('annotator', Hypothesis)
