class Hypothesis extends Annotator
  # Events - overridden for good measure. Unused in the angular Annotator.
  events: {}

  # Plugin configuration
  options:
    Heatmap: {}
    Permissions:
      permissions:
        read: ['group:__world__']
      showEditPermissionsCheckbox: false,
      showViewPermissionsCheckbox: false,
      userString: (user) -> user.replace(/^acct:(.+)@(.+)$/, '$1 on $2')

  # Internal state
  visible: false      # *  Whether the sidebar is visible

  # Here as a noop just to make the Permissions plugin happy
  # XXX: Change me when Annotator stops assuming things about viewers
  viewer:
    addField: (-> )

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
      permissions = @plugins.Permissions
      annotation.user = permissions.options.userId(permissions.user)
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

    # Update the thread when an annotation changes
    this.subscribe 'annotationUpdated', (annotation) =>
      $rootScope.$apply ->
        (threading.getContainer annotation.id).message =
          annotation: annotation
          id: annotation.id
          references: annotation.thread?.split '/'

    # Update the heatmap when the host is updated or annotations are loaded
    bridge = @plugins.Bridge
    heatmap = @plugins.Heatmap
    for event in ['hostUpdated', 'annotationsLoaded']
      this.subscribe event, =>
        @provider.call
          method: 'getHighlights'
          success: ({highlights, offset}) ->
            heatmap.updateHeatmap
              highlights:
                for hl in highlights when hl.data
                  annotation = bridge.cache[hl.data]
                  angular.extend hl, data: annotation
              offset: offset

  _setupXDM: ->
    $location = @element.injector().get '$location'
    $rootScope = @element.injector().get '$rootScope'
    $window = @element.injector().get '$window'
    threading = @element.injector().get 'threading'

    this.addPlugin 'Bridge',
      origin: $location.search().xdm
      window: $window.parent
      formatter: (annotation) =>
        formatted = {}
        for k, v of annotation when k in ['quote', 'ranges']
          formatted[k] = v
        formatted
      parser: (annotation) =>
        parsed = {}
        for k, v of annotation when k in ['quote', 'ranges']
          parsed[k] = v
        parsed

    @provider = Channel.build
      origin: $location.search().xdm
      scope: 'annotator:panel'
      window: $window.parent
      onReady: =>
        patch_update = (store) =>
          # When the store plugin finishes a request, update the annotation
          # using a monkey-patched update function which updates the threading
          # if the annotation has a newly-assigned id and ensures that the id
          # is enumerable.
          store.updateAnnotation = (annotation, data) =>
            bridge = @plugins.Bridge
            $rootScope.$apply ->
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
                if annotation.ranges?.length
                  bridge.deleteAnnotation annotation
                  bridge.setupAnnotation data

                # The id is no longer temporary and should be serialized
                # on future Store requests.
                Object.defineProperty annotation, 'id',
                  configurable: true
                  enumerable: true
                  writable: true

                # If the annotation is loaded in a view, switch the view
                # to reference the new id.
                search = $location.search()
                if search? and search.id == annotation.id
                  search.id = data.id
                  $location.search(search).replace()

              # Update the annotation with the new data
              annotation = angular.extend annotation, data

            # Reflect the newest information in the heatmap
            this.publish 'hostUpdated'

        # Get the location of the annotated document
        @provider.call
          method: 'getHref'
          success: (href) =>
            this.addPlugin 'Store',
              annotationData:
                uri: href
              loadFromSearch:
                limit: 1000
                uri: href
              prefix: '/api/current'
            patch_update this.plugins.Store

        # Dodge toolbars [DISABLE]
        #@provider.getMaxBottom (max) =>
        #  @element.css('margin-top', "#{max}px")
        #  @element.find('#toolbar').css("top", "#{max}px")
        #  @element.find('#gutter').css("margin-top", "#{max}px")
        #  @plugins.Heatmap.BUCKET_THRESHOLD_PAD += max

        this.publish 'hostUpdated'

    @provider

    .bind('publish', (ctx, args...) => this.publish args...)

    .bind('back', =>
      # This guy does stuff when you "back out" of the interface.
      # (Currently triggered by a click on the source page.)
      return unless drafts.discard()
      if $location.path() == '/viewer' and $location.search()?.id?
        $rootScope.$apply => $location.search('id', null).replace()
      else
        this.hide()
    )

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

  setupAnnotation: (annotation) ->
    # This is needed until Annotator stops assuming ranges and highlights
    # are always added.
    unless annotation.ranges?
      annotation.highlights = []
      annotation.ranges = []

    # Assign a temporary id if necessary
    unless annotation.id?
      Object.defineProperty annotation, 'id',
        configurable: true
        enumerable: false
        writable: true
        value: window.btoa Math.random()

    # Thread it
    threading = @element.injector().get 'threading'
    thread = (threading.getContainer annotation.id)
    if thread.message?.annotation
      angular.extend thread.message.annotation, annotation
    else
      thread.message =
        annotation: annotation
        id: annotation.id
        references: annotation.thread?.split('/')

  showViewer: (annotations=[]) =>
    @element.injector().invoke [
      '$location', '$rootScope',
      ($location, $rootScope) ->
        $rootScope.annotations = annotations
        $location.path('/viewer').replace()
        $rootScope.$digest()
    ]
    this.show()

  showEditor: (annotation) =>
    @element.injector().invoke [
      '$location', '$rootScope',
      ($location, $rootScope) ->
        $location.path('/editor')
        .search
          id: annotation.id
        .replace()
        $rootScope.$digest()
    ]
    this.show()
    this

  show: =>
    @visible = true
    @provider.notify method: 'showFrame'
    @element.find('#toolbar').addClass('shown')
      .find('.tri').attr('draggable', true)

  hide: =>
    @lastWidth = window.innerWidth
    @visible = false
    @provider.notify method: 'setActiveHighlights'
    @provider.notify method: 'hideFrame'
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
