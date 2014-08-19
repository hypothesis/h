imports = ['h.identity', 'h.services']


class Head
  # Annotation context
  entities: null             # Map<string,Array> of source URIs to clients
  focused: null              # Map<string,Object> of ids to annotations
  clients: null              # Array of all connected frames
  host: null                 # The client that hosts the widget

  # Tool state
  tool: 'comment'            # The active tool (comment or highlighter)
  highlights: false          # Whether to show highlights

  constructor: (@annotator, @drafts, @identity) ->
    @entities = []
    @focused = []
    @clients = []

  addClient: (client) ->
    @clients.push client

    # Export methods
    client
    .bind('open', this.open)
    .bind('back', this.back)
    .bind('showEditor', this.showEditor)
    .bind('showViewer', this.showViewer)
    .bind('updateViewer', this.updateViewer)
    .bind('toggleViewerSelection', this.toggleViewerSelection)
    .bind('setTool', this.setTool)
    .bind('setHighlights', this.setHighlights)
    .bind('addEmphasis', this.addEmphasis)
    .bind('removeEmphasis', this.addEmphasis)

    # Initialize state
    client.notify(method: 'setTool', params: @tool)
    client.notify(method: 'setHighlights', params: @highlights)

    # Extract entities
    client.call
      method: 'getDocumentInfo',
      success: (info) =>
        @entities[info.uri] ?= []
        @entities[info.uri].push client

        for link in info.metadata.link  when link.href
          @entities[link.href] ?= []
          @entities[link.href].push client

        uris = Object.keys(@entities)
        @annotator.options.Store ?= {}
        @annotator.options.Store.entities = uris

        store = @annotator.plugins.Store
        if store?
          store.options.entities = uris

  focusAnnotation: (annotation) ->
    return if annotation.id in @focused
    @focused[annotation.id] = annotation
    console.log 'focus'
    #this._setFocus()

  blurAnnotation: (annotation) ->
    return unless annotation.id of @focused
    delete @focused[annotation.id]
    console.log 'blur'
    #this._setFocus()

  _setFocus: ->
    for c in @clients
      c.notify
        method: 'setFocusedHighlights'
        params: (a.$$tag for _, a of @focused)

  _getAnnotationsFromTags: (tags=[]) ->
    for tag in tags
      annotation = @annotator.plugins.Bridge.cache[tag]
      continue unless annotation?
      annotation

  _buildReplyList: (annotations=[]) ->
    $filter = @annotator.element.injector().get '$filter'
    for annotation in annotations
      if annotation?
        thread = @annotator.threading.getContainer annotation.id
        children = (r.message for r in (thread.children or []))
        children_sorted = children.sort(@annotator.sortAnnotations).reverse()
        annotation.reply_list = children_sorted
        this._buildReplyList children

  open: (ctx) ->
    console.log 'TODO: send route name'
    @host.notify? method: 'showFrame'

  back: (ctx) ->
    return unless @drafts.discard()
    console.log 'TODO: send route name'
    @host.notify? method: 'hideFrame'

  showEditor: (ctx, tag) ->
    annotation = @annotator.plugins.Bridge.cache[tag]
    return unless annotation?

    @annotator.ongoingEdit = annotation
    @drafts.add annotation
    @host?.notify method: 'showFrame', params: 'editor'

    user = @annotator.plugins.Permissions?.user
    @identity.request() unless user

    @annotator.element.injector().invoke [
      '$location',
      ($location) ->
        $location.path('/edit').replace()
    ]

  showViewer: (ctx, {view, tags, focused}) ->
    return unless @drafts.discard()
    @host?.notify method: 'showFrame', params: 'viewer'
    @annotator.element.injector().invoke [
      '$location', '$rootScope', ($location, $rootScope) ->
        $location.path('/view').replace()
    ]
    this.updateViewer ctx, {view, tags, focused}

  updateViewer: (ctx, {view, tags, focused}) ->
    annotations = this._getAnnotationsFromTags(tags)
    this._buildReplyList annotations

    # Do we have to replace the focused list with this?
    if focused
      # Nuke the old focus list
      @focused = []
      # Add the new elements
      for a in annotations
        this.focusAnnotation a, true
    else
      # Go over the old list, and unfocus the ones
      # that are not on this list
      for a in @focused.slice() when a not in annotations
        this.blurAnnotation a, true

    @annotator.element.injector().invoke [
      '$rootScope', ($rootScope) ->
        $rootScope.annotations = annotations
        $rootScope.applyView view
    ]

  toggleViewerSelection: (ctx, {tags, focused}) ->
    console.log 'toggleViewer called'
    return
    this.toggleViewerSelection this._getAnnotationsFromTags(tags), focused

  setTool: (ctx, name) ->
    return if name is @tool
    return unless @drafts.discard()

    @tool = name
    for c in @clients
      c.notify
        method: 'setTool'
        params: @tool

    if @tool is 'highlight'
      userFilter = true
      user = @annotator.plugins.Permissions?.user
      unless user
        @identity.request()
        this.open()
    else
      userFilter = false

    @annotator.options.Store ?= {}
    @annotator.options.Store.userFilter = userFilter

    store = @annotator.plugins.Store
    if store?
      store.options.userFilter = userFilter

  setHighlights: (ctx, state) ->
    @highlights = state
    for c in @clients
      c.notify
        method: 'setHighlights'
        params: state

  addEmphasis: (ctx, tags) ->
    for a in this._getAnnotationsFromTags tags
      a.$emphasis = true

  removeEmphasis: (ctx, tags) ->
    for a in this._getAnnotationsFromTags tags
      delete a.$emphasis


class HeadProvider
  hostOrigin: '*'       # Origin of the widget host
  whitelist: ['$$tag']  # Property whitelist for frame sync
  formatter: angular.identity
  parser: angular.identity
  sanitize: (annotation) ->
    safe = {}
    safe[k] = v for k, v of annotation when k in @whitelist
    safe

  $get: [
    '$document', '$location', '$rootScope', '$window',
    'annotator', 'drafts', 'identity',
    (
     $document,   $location,   $rootScope,   $window,
     annotator,   drafts,   identity,
    ) ->
      hostOrigin = $location.search()['xdm'] or '*'

      # jschannel chokes on FF and Chrome extension origins.
      if hostOrigin.match /^(chrome-extension|resource):\/\//
        hostorigin = '*'

      if @hostOrigin isnt hostOrigin and @hostOrigin isnt '*'
        throw new Error "Host #{hostOrigin} disallowed by #{@hostOrigin}"

      instance = new Head(annotator, drafts, identity)

      # Set up the bridge plugin, which bridges the main annotation methods
      # between the host page and the panel widget.
      annotator.addPlugin 'Bridge',
        origin: hostOrigin
        gateway: true
        formatter: (annotation) => this.formatter(this.sanitize(annotation))
        parser: (annotation) => this.parser(this.sanitize(annotation))
        onConnect: (source, origin, scope) =>
          # Only support one domain at a time for now
          return unless origin is hostOrigin

          client = Channel.build
            window: source
            origin: origin
            scope: "#{scope}:provider"
            onReady: -> instance.host = client if source is $window.parent

          # Bind calls as methods in the context of the service instance.
          client.bind = ((bind, self) ->
            (name, fn) ->
              bind.call client, name, (args...) ->
                $rootScope.$apply ->
                  fn.apply self, args
          )(client.bind, instance)

          instance.addClient(client)

      $rootScope.activate = (annotation) ->
        if angular.isArray annotation
          highlights = (a.$$tag for a in annotation when a?)
        else if angular.isObject annotation
          highlights = [annotation.$$tag]
        else
          highlights = []

        for c in instance.clients
          c.notify
            method: 'setActiveHighlights'
            params: highlights

      $rootScope.$on 'focus', (event) ->
        for c in instance.clients
          c.notify
            method: 'scrollTo'
            params: event.targetScope.annotation.$$tag

      $rootScope.$watch 'persona', (value) =>
        unless value
          instance.setTool 'comment'

      $rootScope.$watch 'viewState.view', (view) ->
        return unless view
        {method, params} = switch view
          when 'Screen'
              method: 'setDynamicBucketMode', params: true
          when 'Document'
              method: 'showAll'
          when 'Comments', 'Selection'
              method: 'setDynamicBucketMode', params: false
        c.notify {method, params} for c in instance.clients

      # Support the host in resizing the frame
      $document.on 'dragover', (event) =>
        instance.host?.notify
          method: 'dragFrame'
          params: event.screenX

      # Return the instance
      instance
  ]

angular.module('h.widget.head', imports).provider('head', HeadProvider)
