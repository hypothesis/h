class CrossFrameSync

  # Default configuration
  options:

    # Origins allowed to communicate on the channel
    origin: '*'

    # Scope identifier to distinguish this channel from any others
    scope: 'annotator:bridge'

    # When this is true, this bridge will act as a gateway and, similar to DHCP,
    # offer to connect to bridges in other frames it discovers.
    gateway: false

    # A callback to invoke when a connection is established. The function is
    # passed two arguments, the source window and origin of the other frame.
    onConnect: -> true

    # Formats an annotation for sending across the bridge
    formatter: (annotation) -> annotation

    # Parses an annotation received from the bridge
    parser: (annotation) -> annotation

    # Merge function. If specified, it will be called with the local copy of
    # an annotation and a parsed copy received as an argument to an RPC call
    # to reconcile any differences. The default behavior is to merge all
    # keys of the remote object into the local copy
    merge: (local, remote) ->
      for k, v of remote
        local[k] = v
      local

  # event: event_handler
  events:
    'beforeAnnotationCreated': 'beforeAnnotationCreated'
    'annotationCreated': 'annotationCreated'
    'annotationUpdated': 'annotationUpdated'
    'annotationDeleted': 'annotationDeleted'
    'annotationsLoaded': 'annotationsLoaded'


  # Cache of annotations which have crossed the bridge for fast, encapsulated
  # association of annotations received in arguments to window-local copies.
  cache: null

  # Connected bridge links
  links: null

  # Annotations currently being updated -- used to avoid event callback loops
  updating: null


  ## TODO this.$inject = ['$rootScope']
  constructor: ($rootScope, options) ->
    @options = $.extend(true, {}, @options, options)
    for own event, functionName of @events
      $rootScope.$on(event, this[functionName])
    $(window).on 'message', this._onMessage
    this._beacon()

    @cache = {}
    @links = []
    @updating = {}

    @$rootScope = $rootScope


  destructor: =>
    $(window).off 'message', this._onMessage

  _emit: (args...) ->
    @$rootScope.$emit.apply(@$rootScope, args)

  getAnnotationForTag: (tag) ->
    @cache[tag] or null

  bind_channel_listeners: (channel) ->
    # Channel message --> trigger events on $rootScope
    channel.bind 'beforeCreateAnnotation', (txn, annotation) =>
      annotation = this._parse annotation
      delete @cache[annotation.$$tag]
      @_emit 'beforeAnnotationCreated', annotation
      @cache[annotation.$$tag] = annotation
      this._format annotation

    channel.bind 'createAnnotation', (txn, annotation) =>
      annotation = this._parse annotation
      delete @cache[annotation.$$tag]
      @_emit 'annotationCreated', annotation
      @cache[annotation.$$tag] = annotation
      this._format annotation

    channel.bind 'updateAnnotation', (txn, annotation) =>
      annotation = this._parse annotation
      delete @cache[annotation.$$tag]
      @_emit('beforeAnnotationUpdated', [annotation])
      @_emit('annotationUpdated', [annotation])
      @cache[annotation.$$tag] = annotation
      this._format annotation

    channel.bind 'deleteAnnotation', (txn, annotation) =>
      annotation = this._parse annotation
      delete @cache[annotation.$$tag]
      @_emit('annotationDeleted', [annotation])
      res = this._format annotation
      delete @cache[annotation.$$tag]
      res

    channel.bind 'sync', (ctx, annotations) =>
      (this._format (this._parse a) for a in annotations)

    ## Notifications
    channel.bind 'loadAnnotations', (txn, annotations) =>
      annotations = (this._parse a for a in annotations)
      @_emit('loadAnnotations', annotations)




  # Handlers for sidebar events on $rootScope. Pass events through channel to guest code.

  beforeAnnotationCreated: (event, annotation) =>
    return if annotation.$$tag?
    this.beforeCreateAnnotation annotation
    this

  annotationCreated: (event, annotation) =>
    return unless annotation.$$tag? and @cache[annotation.$$tag]
    this.createAnnotation annotation
    this

  annotationUpdated: (event, annotation) =>
    return unless annotation.$$tag? and @cache[annotation.$$tag]
    this.updateAnnotation annotation
    this

  annotationDeleted: (event, annotation) =>
    return unless annotation.$$tag? and @cache[annotation.$$tag]
    this.deleteAnnotation annotation, (err) =>
      if err then @annotator.setupAnnotation annotation
      else delete @cache[annotation.$$tag]
    this

  annotationsLoaded: (event, annotations) =>
    annotations = (this._format a for a in annotations when not a.$$tag)
    return unless annotations.length
    this._notify
      method: 'loadAnnotations'
      params: annotations
    this



  ## Common Code

  beforeCreateAnnotation: (annotation, cb) ->
    this._call
      method: 'beforeCreateAnnotation'
      params: this._format annotation
      callback: cb
    annotation

  createAnnotation: (annotation, cb) ->
    this._call
      method: 'createAnnotation'
      params: this._format annotation
      callback: cb
    annotation

  updateAnnotation: (annotation, cb) ->
    this._call
      method: 'updateAnnotation'
      params: this._format annotation
      callback: cb
    annotation

  deleteAnnotation: (annotation, cb) ->
    this._call
      method: 'deleteAnnotation'
      params: this._format annotation
      callback: cb
    annotation


  # Assign a non-enumerable tag to objects which cross the bridge.
  # This tag is used to identify the objects between message.
  _tag: (msg, tag) ->
    return msg if msg.$$tag
    tag = tag or (window.btoa Math.random())
    Object.defineProperty msg, '$$tag', value: tag
    @cache[tag] = msg
    msg

  # Parse an annotation from a RPC with the configured parser
  _parse: ({tag, msg}) ->
    local = @cache[tag]
    remote = @options.parser msg

    if local?
      merged = @options.merge local, remote
    else
      merged = remote

    this._tag merged, tag

  # Format an annotation for RPC with the configured formatter
  _format: (annotation) ->
    this._tag annotation
    msg = @options.formatter annotation
    tag: annotation.$$tag
    msg: msg

  # Construct a channel to another frame
  _build: (options) ->
    # jschannel chokes on FF and Chrome extension origins.
    if (options.origin.match /^chrome-extension:\/\//) or
        (options.origin.match /^resource:\/\//)
      options.origin = '*'

    channel = Channel.build(options)
    @bind_channel_listeners(channel)


  # Send out a beacon to let other frames know to connect to us
  _beacon: ->
    queue = [window.top]
    while queue.length
      parent = queue.shift()
      if parent isnt window
        parent.postMessage '__annotator_dhcp_discovery', @options.origin
      for child in parent.frames
        queue.push child

  # Make a method call on all links
  _call: (options) ->
    _makeDestroyFn = (c) =>
      (error, reason) =>
        c.destroy()
        @links = (l for l in @links when l.channel isnt c)

    deferreds = @links.map (l) ->
      d = $.Deferred().fail (_makeDestroyFn l.channel)
      options = $.extend {}, options,
        success: (result) -> d.resolve result
        error: (error, reason) ->
          if error isnt 'timeout_error'
            d.reject error, reason
          else
            d.resolve null
        timeout: 1000
      l.channel.call options
      d.promise()

    $.when(deferreds...)
    .then (results...) =>
      if Array.isArray(results[0])
        acc = []
        foldFn = (_, cur) =>
          (this._parse(a) for a in cur)
      else
        acc = {}
        foldFn = (_, cur) =>
          this._parse(cur)
      options.callback? null, results.reduce(foldFn, acc)
    .fail (failure) =>
      options.callback? failure

  # Publish a notification to all links
  _notify: (options) ->
    for l in @links
      l.channel.notify options

  _onMessage: (e) =>
    {source, origin, data} = e.originalEvent
    match = data.match? /^__annotator_dhcp_(discovery|ack|offer)(:\d+)?$/
    return unless match

    if match[1] is 'discovery'
      if @options.gateway
        scope = ':' + ('' + Math.random()).replace(/\D/g, '')
        source.postMessage '__annotator_dhcp_offer' + scope, origin
      else
        source.postMessage '__annotator_dhcp_ack', origin
        return
    else if match[1] is 'ack'
      if @options.gateway
        scope = ':' + ('' + Math.random()).replace(/\D/g, '')
        source.postMessage '__annotator_dhcp_offer' + scope, origin
      else
        return
    else if match[1] is 'offer'
      if @options.gateway
        return
      else
        scope = match[2]

    scope = @options.scope + scope
    options = $.extend {}, @options,
      window: source
      origin: origin
      scope: scope
      onReady: =>
        options.onConnect(source, origin, scope)
        annotations = (this._format a for t, a of @cache)
        if annotations.length
          channel.notify
            method: 'loadAnnotations'
            params: annotations

    channel = this._build options

    @links.push
      channel: channel
      window: source
