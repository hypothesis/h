class AnnotationSync
  # Default configuration
  options:
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

  # Handlers for messages arriving through a channel
  channelListeners:
    'beforeCreateAnnotation': (txn, annotation) =>
      annotation = this._parse annotation
      delete @cache[annotation.$$tag]
      @_emit 'beforeAnnotationCreated', annotation
      @cache[annotation.$$tag] = annotation
      this._format annotation

    'createAnnotation': (txn, annotation) =>
      annotation = this._parse annotation
      delete @cache[annotation.$$tag]
      @_emit 'annotationCreated', annotation
      @cache[annotation.$$tag] = annotation
      this._format annotation

    'updateAnnotation': (txn, annotation) =>
      annotation = this._parse annotation
      delete @cache[annotation.$$tag]
      @_emit('beforeAnnotationUpdated', [annotation])
      @_emit('annotationUpdated', [annotation])
      @cache[annotation.$$tag] = annotation
      this._format annotation

    'deleteAnnotation': (txn, annotation) =>
      annotation = this._parse annotation
      delete @cache[annotation.$$tag]
      @_emit('annotationDeleted', [annotation])
      res = this._format annotation
      delete @cache[annotation.$$tag]
      res

    'sync': (ctx, annotations) =>
      (this._format (this._parse a) for a in annotations)

    'loadAnnotations': (txn, annotations) =>
      annotations = (this._parse a for a in annotations)
      @_emit('loadAnnotations', annotations)

  # Cache of annotations which have crossed the bridge for fast, encapsulated
  # association of annotations received in arguments to window-local copies.
  cache: null

  ## TODO this.$inject = ['$rootScope']
  constructor: ($rootScope, options, bridge) ->
    @options = $.extend(true, {}, @options, options)

    @cache = {}
    @$rootScope = $rootScope

    # Listen locally for interesting events
    for event, handler of @eventListeners
      this._on(event, handler)

    onConnect = (channel) =>
      # Upon new connections, send over the items in our cache
      this._syncCache(channel)
    bridge.onConnect(onConnect)

    # Register remotely invokable methods
    for method, func in @channelListeners
      bridge.on(method, func)

  _syncCache: (channel) =>
    # Synchronise (here to there) the items in our cache
    annotations = (this._format a for t, a of @cache)
    if annotations.length
      channel.notify
        method: 'loadAnnotations'
        params: annotations

  _emit: (args...) =>
    @$rootScope.$emit.call(@$rootScope, args...)

  _on: (event, handler) =>
    @$rootScope.$on(event, handler)

  getAnnotationForTag: (tag) ->
    @cache[tag] or null

  # Handlers for events coming from this frame, to send them across the channel
  eventListeners:
    'beforeAnnotationCreated': @beforeAnnotationCreated
    'annotationCreated': @annotationCreated
    'annotationUpdated': @annotationUpdated
    'annotationDeleted': @annotationDeleted
    'annotationsLoaded': @annotationsLoaded


  _mkCallRemotelyAndParseResults: (method, callBack) ->
    fn = (annotation) ->
      # Wrap the callback function to first parse returned items
      wrappedCallback = (failure, results) =>
        unless failure?
          this._parseResults results
        callBack? failure, results

      # Call the remote method
      options =
        method: method
        callback: wrappedCallback
        params: this._format(annotation)
      @bridge.call(options)

  # Handlers for sidebar events on $rootScope. Pass events through channel to guest code.

  beforeAnnotationCreated: (event, annotation) =>
    return if annotation.$$tag?
    this._mkCallRemotelyAndParseResults('beforeCreateAnnotation')(annotation)
    this

  annotationCreated: (event, annotation) =>
    return unless annotation.$$tag? and @cache[annotation.$$tag]
    this._mkCallRemotelyAndParseResults('createAnnotation')(annotation)
    this

  annotationUpdated: (event, annotation) =>
    return unless annotation.$$tag? and @cache[annotation.$$tag]
    this._mkCallRemotelyAndParseResults('updateAnnotation')(annotation)
    this

  annotationDeleted: (event, annotation) =>
    return unless annotation.$$tag? and @cache[annotation.$$tag]
    onFailure = (err) =>
      if err then @annotator.setupAnnotation annotation # TODO
      else delete @cache[annotation.$$tag]
    this._mkCallRemotelyAndParseResults('deleteAnnotation', onFailure)(annotation)
    this

  annotationsLoaded: (event, annotations) =>
    annotations = (this._format a for a in annotations when not a.$$tag)
    return unless annotations.length
    this._notify
      method: 'loadAnnotations'
      params: annotations
    this

  # Parse returned annotations to update cache with any changes made remotely
  _parseResults: (results) ->
    if Array.isArray(results[0])
      acc = []
      foldFn = (_, cur) =>
        (this._parse(a) for a in cur)
    else
      acc = {}
      foldFn = (_, cur) =>
        this._parse(cur)
    results.reduce(foldFn, acc)

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
    {
      tag: annotation.$$tag
      msg: msg
    }
