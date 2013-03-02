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

    # Set up XDM connection
    this._setupXDM()

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
    this.subscribe 'annotationDeleted', (annotation) =>
      $rootScope.$apply ->
        thread = threading.getContainer annotation.id
        thread.message = null
        if thread.parent then threading.pruneEmpties thread.parent

    # Thread the annotations after loading
    this.subscribe 'annotationsLoaded', (annotations) =>
      $rootScope.$apply ->
        threading.thread annotations.map (a) ->
          annotation: a
          id: a.id
          references: a.thread?.split '/'

    # After annotations were loaded (or none was found), scan the document
    for event in ['annotationsLoaded', 'foundNoAnnotations']
      this.subscribe event, =>        
        $rootScope.$apply =>
          @provider.scanDocument "annotations were loaded (if any)"


    # Update the thread when an annotation changes
    this.subscribe 'annotationUpdated', (annotation) =>
      $rootScope.$apply ->
        (threading.getContainer annotation.id).message =
          annotation: annotation
          id: annotation.id
          references: annotation.thread?.split '/'

    # Update the heatmap when the host is updated or annotations are loaded
    heatmap = @plugins.Heatmap
    for event in ['hostUpdated', 'annotationsLoaded']
      this.subscribe event, =>
        @provider.getHighlights ({highlights, offset}) ->
          $rootScope.$apply ->
            heatmap.updateHeatmap
              highlights: highlights.map (hl) ->
                thread = (threading.getContainer hl.data.id)
                hl.data = thread.message?.annotation
                hl
              offset: offset

  _setupXDM: ->
    $scope = @element.scope()
    $location = @element.injector().get '$location'
    threading = @element.injector().get 'threading'

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
            {deleteAnnotation, loadAnnotations} = @provider
            $scope.$apply ->
              if annotation.id != data.id
                # Remove the old annotation from the threading
                thread = (threading.getContainer annotation.id)
                if thread.parent
                  thread.message = null
                  threading.pruneEmpties thread.parent
                else
                  delete threading.idTable[annotation.id]

                # Create the new thread
                thread = (threading.getContainer data.id)
                references = data.thread?.split('/') or []
                thread.message =
                  annotation: annotation
                  id: data.id
                  references: references

                if not thread.parent? and thread.message.references.length
                  threading.getContainer(references[references.length-1])
                  .addChild thread

                # Remove the old annotation from the host.
                # XXX in iframe mode it's safe to make these calls because the
                # deletion event that gets published in the provider is not
                # cross-published back here in the consumer and therefore
                # the Store does not delete the annotation.
                # XXX Maybe add provider function for updating id
                deleteAnnotation
                  id: annotation.id
                loadAnnotations [
                  id: data.id
                  target: data.target
                  quote: data.quote
                ]

                # The id is no longer temporary and should be serialized
                # on future Store requests.
                Object.defineProperty annotation, 'id',
                  enumerable: true

                # If the annotation is loaded in a view, switch the view
                # to reference the new id.
                search = $location.search()
                if search? and search.id == annotation.id
                  search.id = data.id
                  $location.search(search).replace()

              # Update the annotation with the new data
              annotation = angular.extend annotation, data

            this.publish 'hostUpdated'

        # Dodge toolbars [DISABLE]
        #@provider.getMaxBottom (max) =>
        #  @element.css('margin-top', "#{max}px")
        #  @element.find('#toolbar').css("top", "#{max}px")
        #  @element.find('#gutter').css("margin-top", "#{max}px")
        #  @plugins.Heatmap.BUCKET_THRESHOLD_PAD += max

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
            $scope.$apply => $scope.$broadcast 'showAuth'
            this.show()
            null
        showEditor: (annotation) =>
          thread = (threading.getContainer annotation.id)
          if thread.message?.annotation
            angular.extend thread.message.annotation, annotation
          else
            thread.message =
              annotation: annotation
              id: annotation.id
              references: annotation.thread?.split('/')
          $scope.$apply => this.showEditor thread.message.annotation
          this.show()
        showViewer: (annotations) =>
          annotations = for a in annotations
            thread = (threading.getContainer a.id)
            thread.message?.annotation or a
          $scope.$apply => this.showViewer annotations
          this.show()
        back: => $scope.$apply => $scope.$broadcast 'back'
        update: => this.publish 'hostUpdated'
      remote:
        publish: {}
        setupAnnotation: {}
        deleteAnnotation: {}
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
        scanDocument: {}

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

  # Override things not used in the angular version.
  _setupDynamicStyle: -> this
  _setupViewer: -> this
  _setupEditor: -> this

  createAnnotation: ->
    annotation = super

    # Assign temporary ids to newly created annotations. It is temporary
    # by virtue of not being serialized (non-enumerable) and clobbered
    # later, after saving. Use a base64 encoding the JSON representation.
    Object.defineProperty annotation, 'id',
      configurable: true
      enumerable: false
      writable: true
      value: window.btoa (JSON.stringify annotation + Math.random())

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
    # targets. This is needed until Annotator stops assuming targets need to be
    # added.
    if annotation.thread
      annotation.target = []
    else
      unless annotation.target instanceof Array
        annotation.target = [annotation.target]
      @provider.setupAnnotation
        id: annotation.id
        target: annotation.target
      annotation.quote = this.getQuoteForTarget annotation.target[0]

  showViewer: (annotations=[]) =>
    @element.injector().invoke [
      '$location', '$rootScope',
      ($location, $rootScope) ->
        $rootScope.annotations = annotations
        $location.path('/viewer')
        .replace()
    ]

  showEditor: (annotation) =>
    @element.injector().invoke [
      '$location',
      ($location) ->
        $location.path('/editor')
        .search
          id: annotation.id
        .replace()
    ]

  show: =>
    @provider.showFrame()
    @element.find('#toolbar').addClass('shown')
      .find('.tri').attr('draggable', true)

  hide: =>
    @lastWidth = window.innerWidth
    @provider.setActiveHighlights []
    @provider.hideFrame()
    @element.find('#toolbar').removeClass('shown')
      .find('.tri').attr('draggable', false)


class DraftProvider
  drafts: []

  $get: -> this
  add: (draft) -> @drafts.push draft unless this.contains draft
  remove: (draft) -> @drafts = (d for d in @drafts when d isnt draft)
  contains: (draft) -> (@drafts.indexOf draft) != -1

  discard: ->
    count = (d for d in @drafts when d.text?.length).length
    text =
      switch count
        when 0 then null
        when 1
          """You have an unsaved reply.

          Do you really want to discard this draft?"""
        else
          """You have #{count} unsaved replies.

          Do you really want to discard these drafts?"""

    if count == 0 or confirm text
      @drafts = []
      true
    else
      false


class FlashProvider
  queues:
    info: []
    error: []
    success: []
  notice: null
  timeout: null

  constructor: ->
    # Configure notification classes
    angular.extend Annotator.Notification,
      INFO: 'info'
      ERROR: 'error'
      SUCCESS: 'success'

  _process: ->
    @timeout = null
    for q, msgs of @queues
      if msgs.length
        notice = Annotator.showNotification msgs.shift(), q
        @timeout = this._wait =>
          # work around Annotator.Notification not removing classes
          for _, klass of notice.options.classes
            notice.element.removeClass klass
          this._process()
        break

  $get: ['$timeout', 'annotator', ($timeout, annotator) ->
    this._wait = (cb) -> $timeout cb, 5000
    angular.bind this, this._flash
  ]

  _flash: (queue, messages) ->
    if @queues[queue]?
      @queues[queue] = @queues[queue]?.concat messages
      this._process() unless @timeout?


angular.module('h.services', [])
  .provider('drafts', DraftProvider)
  .provider('flash', FlashProvider)
  .service('annotator', Hypothesis)
  .value('threading', mail.messageThread())
