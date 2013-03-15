# node style callback helpers
success = (cb) -> (result) -> cb? null, result
error = (cb) -> (error, reason) -> cb? {error: error, reason: reason}


class Annotator.Plugin.Bridge extends Annotator.Plugin

  # Plugin configuration
  options:

    # Origins allowed to communicate on the channel
    origin: '*'

    # Scope identifier to distinguish this channel from any others
    scope: 'annotator:bridge'

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

  # Cache of annotations which have crossed the bridge for fast, encapsulated
  # association of annotations received in arguments to window-local copies.
  cache: {}

  pluginInit: ->
    @options.onReady = this.onReady
    @channel = Channel.build @options

    # Set up annotations on the other side of the bridge when necessary
    @annotator.subscribe 'beforeAnnotationCreated', (annotation) =>
      this.setupAnnotation annotation
    @annotator.subscribe 'annotationsLoaded', (annotations) =>
      this.setupAnnotation a for a in annotations

    # Prevent the cache from leaking annotation references
    @annotator.subscribe 'annotationDeleted', (annotation) =>
      if annotation.$$tag? then delete @cache[annotation.$$tag]

  # Assign a non-enumerable tag to objects which cross the bridge.
  # This tag is used to identify the objects between message.
  _tag: (msg, tag) ->
    return msg if msg.$$tag
    tag = tag or (window.btoa Math.random())
    Object.defineProperty msg, '$$tag', value: tag
    @cache[tag] = msg
    msg

  # Call the configured parser and tag the result
  _parse: ({tag, msg}) ->
    local = @cache[tag]
    remote = @options.parser msg

    if local?
      merged = @options.merge local, remote
    else
      merged = remote

    this._tag merged, tag

  # Tag the object and format it with the configured formatter
  _format: (annotation) ->
    this._tag annotation
    msg = @options.formatter annotation
    tag: annotation.$$tag
    msg: msg

  onReady: =>
    @channel

    ## Remote method call bindings
    .bind('createAnnotation', (txn) =>
      this._format @annotator.createAnnotation()
    )

    .bind('setupAnnotation', (txn, annotation) =>
      this._format (@annotator.setupAnnotation (this._parse annotation))
    )

    .bind('updateAnnotation', (txn, annotation) =>
      this._format (@annotator.updateAnnotation (this._parse annotation))
    )

    ## Notifications
    .bind('deleteAnnotation', (ctx, annotation) =>
      @annotator.deleteAnnotation (this._parse annotation)
    )

    .bind('showEditor', (ctx, annotation) =>
      @annotator.showEditor (this._parse annotation)
    )

    .bind('showViewer', (ctx, annotations) =>
      @annotator.showEditor (this._parse a for a in annotations)
    )

  createAnnotation: (cb) ->
    @channel.call
      method: 'createAnnotation'
      success: success cb
      error: error cb

  setupAnnotation: (annotation, cb) ->
    @channel.call
      method: 'setupAnnotation'
      params: this._format annotation
      success: success cb
      error: error cb

  updateAnnotation: (annotation, cb) ->
    @channel.call
      method: 'updateAnnotation'
      params: this._format annotation
      success: success cb
      error: error cb

  deleteAnnotation: (annotation, cb) ->
    @channel.notify
      method: 'deleteAnnotation'
      params: this._format annotation

  showEditor: (annotation) ->
    @channel.notify
      method: 'showEditor'
      params: this._format annotation

  showViewer: (annotations) ->
    @channel.notify
      method: 'showViewer'
      params: (this._format a for a in annotations)
