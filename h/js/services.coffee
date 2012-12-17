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
  visible: false     # * Whether the sidebar is visible
  unsaved_drafts: [] # * Unsaved drafts currenty open

  this.$inject = [
    '$document', '$location', '$rootScope',
    'threading'
  ]
  constructor: (
    $document, $location, $rootScope,
    threading
  ) ->
    super ($document.find 'body')
    # Load plugins
    for own name, opts of @options
      if not @plugins[name] and name of Annotator.Plugin
        this.addPlugin(name, opts)

    # Add user info to new annotations
    this.subscribe 'beforeAnnotationCreated', (annotation) =>
      annotation.user = @plugins.HypothesisPermissions.options.userId(
        @plugins.HypothesisPermissions.user)
      Object.defineProperty annotation, 'draft',
        configurable: true
        enumerable: false
        writable: true
        value: true

    # Update threads when annotations are deleted
    this.subscribe 'annotationDeleted', (annotation) ->
      debugger
      thread = threading.getContainer annotation.id
      thread.message = null
      if thread.parent then threading.pruneEmpties thread.parent

    # Thread the annotations after loading
    this.subscribe 'annotationsLoaded', (annotations) ->
      threading.thread annotations.map (a) ->
        annotation: a
        id: a.id
        references: a.thread?.split '/'

    # Update the thread when an annotation changes
    this.subscribe 'annotationUpdated', (annotation) ->
      (threading.getContainer annotation.id).message =
        annotation: annotation
        id: annotation.id
        references: annotation.thread?.split '/'

    # Establish cross-domain communication to the widget host
    @provider = new easyXDM.Rpc
      swf: @options.swf
      onReady: =>
        # Get the location of the annotated document
        @provider.getHref (href) =>
          this.addPlugin 'Store',
            annotationData:
              uri: href
            loadFromSearch:
              limit: 1000
              uri: href
            prefix: '/api/current'

          # When the store plugin finishes a request, update the annotation
          # using a monkey-patched update function which updates the threading
          # if the annotation has a newly-assigned id and ensures that the id
          # is enumerable.
          this.plugins.Store.updateAnnotation = (annotation, data) =>
            if annotation.id != data.id
              # Remove the old annotation from the threading
              thread = (threading.getContainer annotation.id)
              thread.message = null
              threading.pruneEmpties thread.parent

            # Update the annotation with the new data
            annotation = angular.extend annotation, data

            # Update the thread
            thread = (threading.getContainer data.id)
            references = annotation.thread?.split('/') or []
            thread.message =
              annotation: annotation
              id: annotation.id
              references: references

            if thread.message.references.length
              parent = (threading.getContainer references[references.length-1])
              parent.addChild thread

            @provider.loadAnnotations [
              id: annotation.id
              ranges: annotation.ranges
              quote: annotation.quote
            ]

            Object.defineProperty annotation, 'id',
              enumerable: true

            $rootScope.$apply()

        @provider.getMaxBottom (max) =>
          @element.find('#toolbar').css("top", "#{max}px")
          @element.find('#gutter').css("margin-top", "#{max}px")
          @plugins.Heatmap.BUCKET_THRESHOLD_PAD += max

        this.publish 'hostUpdated'
    ,
      local:
        publish: (args..., k, fk) => this.publish args...
        addPlugin: => this.addPlugin arguments...
        createAnnotation: =>
          if @plugins.HypothesisPermissions.user?
            annotation = this.createAnnotation()
            thread = (threading.getContainer annotation.id)
            thread.message =
              annotation: annotation
              id: annotation.id
              references: []
            annotation.id
          else
            $rootScope.$apply => $rootScope.$broadcast 'showAuth'
            this.show()
            null
        showEditor: (annotation) =>
          return unless this._canCloseUnsaved()
          thread = (threading.getContainer annotation.id)
          if thread.message?.annotation
            angular.extend thread.message.annotation, annotation
          else
            thread.message =
              annotation: annotation
              id: annotation.id
              references: annotation.thread?.split('/')
          this.showEditor thread.message.annotation
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
        loadAnnotations: {}
        onEditorHide: {}
        onEditorSubmit: {}
        showFrame: {}
        hideFrame: {}
        dragFrame: {}
        getHighlights: {}
        setActiveHighlights: {}
        getHref: {}
        getMaxBottom: {}
        scrollTop: {}

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
    @element.append el

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

  createAnnotation: ->
    annotation = super

    # Assign temporary ids to newly created annotations. It is temporary
    # by virtue of not being serialized (non-enumerable) and clobbered
    # later, after saving. Use a base64 encoding the JSON representation.
    Object.defineProperty annotation, 'id',
      configurable: true
      enumerable: false
      writable: true
      value: window.btoa (JSON.stringify annotation)

    annotation

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

    @provider.setupAnnotation
      id: annotation.id
      ranges: annotation.ranges

  showViewer: (annotations=[], detail=false) =>
    if (@visible and not detail) or @unsaved_drafts.indexOf(@editor) > -1
      if not this._canCloseUnsaved() then return

    # Not implemented

  showEditor: (annotation) =>
    @element.injector().invoke [
      '$location', '$rootScope',
      ($location, $rootScope) =>
        $rootScope.$apply =>
          $location.path('/editor')
            .search
              id: annotation.id
            .replace()
    ]
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
  .value('threading', mail.messageThread())
