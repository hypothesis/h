# Uses a channel between the sidebar and the attached providers to ensure
# the interface remains in sync.
class CrossFrameUIService
  # Internal state
  providers: null
  host: null

  this.$inject = ['$document', '$window', 'store', 'toolkit', '$rootScope', 'threading']
  constructor:   ( $document,   $window,   store ,  toolkit,   $rootScope,   threading) ->
    $rootScope.$on('annotationDeleted', this.annotationDeleted)

    @providers = []
    @toolkit = toolkit

    this._emit = (event, args...) ->
      $rootScope.$emit(event, args...)

    # Set up the bridge plugin, which bridges the main annotation methods
    # between the host page and the panel widget.
    whitelist = ['target', 'document', 'uri']
    bridge = new CrossFrameSync $rootScope,
      gateway: true
      formatter: (annotation) ->
        formatted = {}
        for k, v of annotation when k in whitelist
          formatted[k] = v
        formatted
      parser: (annotation) ->
        parsed = new store.AnnotationResource()
        for k, v of annotation when k in whitelist
          parsed[k] = v
        parsed
      onConnect: (source, origin, scope) =>
        options =
          window: source
          origin: origin
          scope: "#{scope}:provider"
          onReady: => if source is $window.parent then @host = channel
        channel = this._setupXDM options
        provider = channel: channel, entities: []

        channel.call
          method: 'getDocumentInfo'
          success: (info) =>
            provider.entities = (link.href for link in info.metadata.link)
            @providers.push(provider)
            this._emit('getDocumentInfo')

        # Allow the host to define it's own state
        unless source is $window.parent
          channel.notify
            method: 'setTool'
            params: @toolkit.tool

          channel.notify
            method: 'setVisibleHighlights'
            params: @toolkit.visibleHighlights

    this.getAnnotationsByTags = (tags) ->
      tags.map(bridge.getAnnotationForTag, bridge)

  _setupXDM: (options) ->
    # jschannel chokes FF and Chrome extension origins.
    if (options.origin.match /^chrome-extension:\/\//) or
        (options.origin.match /^resource:\/\//)
      options.origin = '*'

    provider = Channel.build(options)

    provider.bind 'back', =>
      # Navigate "back" out of the interface.
      this.hide()

    provider.bind 'open', =>
      this.show()

    provider.bind 'showEditor', (ctx, tag) =>
      this.show()

    provider.bind 'showAnnotations', (ctx, tags=[]) =>
      this.show()
      this._emit('showAnnotations', tags)
      annotations = this.getAnnotationsByTags(tags)
      toolkit.mergeSelectedAnnotations(annotations)

    provider.bind 'focusAnnotations', (ctx, tags=[]) =>
      this._emit('focusAnnotations', tags)
      annotations = this.getAnnotationsByTags(tags)
      toolkit.focusedAnnotations = annotations

    provider.bind 'toggleAnnotationSelection', (ctx, tags=[]) =>
      this._emit('toggleViewerSelection', tags)
      annotations = this.getAnnotationsByTags(tags)
      toolkit.selectedAnnotations = annotations

    provider.bind 'setTool', (ctx, name) =>
      @toolkit.tool = name
      for p in @providers
        p.channel.notify({
          method: 'setTool'
          params: name
        })

    provider.bind 'setVisibleHighlights', (ctx, state) =>
      @toolkit.visibleHighlights = Boolean(state)
      for p in @providers
        p.channel.notify({
          method: 'setVisibleHighlights'
          params: state
        })

  _setupDocumentEvents: ->
    $document.addEventListener 'dragover', (event) =>
      @host?.notify
        method: 'dragFrame'
        params: event.screenX
    this

  show: ->
    @host.notify(method: 'showFrame')

  hide: ->
    @host.notify(method: 'hideFrame')

angular.module('h').service('crossFrameUI', CrossFrameUIService)
