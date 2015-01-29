class AnnotationSync
  # Default configuration
  options:
    # Formats an annotation into a message body for sending across the bridge.
    formatter: (annotation) -> annotation

    # Recieves an annotation extracted from the message body received
    # via the bridge and returns an annotation for use in the local app.
    parser: (annotation) -> annotation

    # Merge function. If specified, it will be called with the local copy of
    # an annotation and a parsed copy received as an argument to an RPC call
    # to reconcile any differences. The default behavior is to merge all
    # keys of the remote object into the local copy
    merge: (local, remote) ->
      for k, v of remote
        local[k] = v
      local

    # Function used to emit annotation events
    emit: (event, args...) ->
      throw new Error('options.emit unspecified for AnnotationSync.')

    # Function used to register handlers for annotation events
    on: (event, handler) ->
      throw new Error('options.on unspecified for AnnotationSync.')

  # Cache of annotations which have crossed the bridge for fast, encapsulated
  # association of annotations received in arguments to window-local copies.
  cache: null

  constructor: (options, @bridge) ->
    @options = $.extend(true, {}, @options, options)

    @cache = {}

    @_on = @options.on
    @_emit = @options.emit

    # Listen locally for interesting events
    for event, handler of @_eventListeners
      this._on(event, handler.bind(this))

    # Register remotely invokable methods
    for method, func of @_channelListeners
      @bridge.on(method, func.bind(this))

    # Upon new connections, send over the items in our cache
    onConnect = (channel) =>
      this._syncCache(channel)
    @bridge.onConnect(onConnect)

  # Provide a public interface to the annotation cache so that other
  # sync services can lookup annotations by tag.
  getAnnotationForTag: (tag) ->
    @cache[tag] or null

  sync: (annotations, cb) ->
    annotations = (this._format a for a in annotations)
    @bridge.call
      method: 'sync'
      params: annotations
      callback: cb
    this

  # Handlers for messages arriving through a channel
  _channelListeners:
    'beforeCreateAnnotation': (txn, body) ->
      annotation = this._parse(body)
      delete @cache[annotation.$$tag]
      @_emit 'beforeAnnotationCreated', annotation
      @cache[annotation.$$tag] = annotation
      this._format annotation

    'createAnnotation': (txn, body) ->
      annotation = this._parse(body)
      delete @cache[annotation.$$tag]
      @_emit 'annotationCreated', annotation
      @cache[annotation.$$tag] = annotation
      this._format annotation

    'updateAnnotation': (txn, body) ->
      annotation = this._parse(body)
      delete @cache[annotation.$$tag]
      @_emit('beforeAnnotationUpdated', annotation)
      @_emit('annotationUpdated', annotation)
      @cache[annotation.$$tag] = annotation
      this._format annotation

    'deleteAnnotation': (txn, body) ->
      annotation = this._parse(body)
      delete @cache[annotation.$$tag]
      @_emit('annotationDeleted', annotation)
      res = this._format(annotation)
      res

    'sync': (ctx, bodies) ->
      (this._format(this._parse(b)) for b in bodies)

    'loadAnnotations': (txn, bodies) ->
      annotations = (this._parse(a) for a in bodies)
      @_emit('loadAnnotations', annotations)

  # Handlers for events coming from this frame, to send them across the channel
  _eventListeners:
    'beforeAnnotationCreated': (annotation) ->
      return if annotation.$$tag?
      this._mkCallRemotelyAndParseResults('beforeCreateAnnotation')(annotation)

    'annotationCreated': (annotation) ->
      return unless annotation.$$tag? and @cache[annotation.$$tag]
      this._mkCallRemotelyAndParseResults('createAnnotation')(annotation)

    'annotationUpdated': (annotation) ->
      return unless annotation.$$tag? and @cache[annotation.$$tag]
      this._mkCallRemotelyAndParseResults('updateAnnotation')(annotation)

    'annotationDeleted': (annotation) ->
      return unless annotation.$$tag? and @cache[annotation.$$tag]
      onFailure = (err) =>
        delete @cache[annotation.$$tag] unless err
      this._mkCallRemotelyAndParseResults('deleteAnnotation', onFailure)(annotation)

    'annotationsLoaded': (annotations) ->
      bodies = (this._format a for a in annotations when not a.$$tag)
      return unless bodies.length
      @bridge.notify
        method: 'loadAnnotations'
        params: bodies

  _syncCache: (channel) ->
    # Synchronise (here to there) the items in our cache
    annotations = (this._format a for t, a of @cache)
    if annotations.length
      channel.notify
        method: 'loadAnnotations'
        params: annotations

  _mkCallRemotelyAndParseResults: (method, callBack) ->
    (annotation) =>
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

  # Parse returned message bodies to update cache with any changes made remotely
  _parseResults: (results) ->
    for bodies in results
      bodies = [].concat(bodies) # Ensure always an array.
      this._parse(body) for body in bodies when body != null
    return

  # Assign a non-enumerable tag to objects which cross the bridge.
  # This tag is used to identify the objects between message.
  _tag: (ann, tag) ->
    return ann if ann.$$tag
    tag = tag or window.btoa(Math.random())
    Object.defineProperty(ann, '$$tag', value: tag)
    @cache[tag] = ann
    ann

  # Parse a message body from a RPC call with the provided parser.
  _parse: (body) ->
    local = @cache[body.tag]
    remote = @options.parser(body.msg)

    if local?
      merged = @options.merge(local, remote)
    else
      merged = remote

    this._tag(merged, body.tag)

  # Format an annotation into an RPC message body with the provided formatter.
  _format: (ann) ->
    this._tag(ann)
    {
      tag: ann.$$tag
      msg: @options.formatter(ann)
    }

angular?.module('h').value('AnnotationSync', AnnotationSync)
