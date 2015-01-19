# Uses a channel between the sidebar and the attached providers to ensure
# the interface remains in sync.
class CrossFrameUI
  # Internal state
  providers: null
  host: null

  tool: 'comment'
  visibleHighlights: false

  this.$inject = ['$document', '$window', 'store', '$rootScope', 'threading']
  constructor:   ( $document,   $window,   store ,  $rootScope,   threading) ->
    $rootScope.$on('annotationDeleted', this.annotationDeleted)

    @providers = []
    @store = store

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
        parsed = new store.annotation()
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
            $rootScope.$emit('getDocumentInfo')

        # Allow the host to define it's own state
        unless source is $window.parent
          channel.notify
            method: 'setTool'
            params: this.tool

          channel.notify
            method: 'setVisibleHighlights'
            params: this.visibleHighlights

  _setupXDM: (options) ->
    # jschannel chokes FF and Chrome extension origins.
    if (options.origin.match /^chrome-extension:\/\//) or
        (options.origin.match /^resource:\/\//)
      options.origin = '*'

    provider = Channel.build options

    .bind('back', =>
      # Navigate "back" out of the interface.
      this.hide()
    )

    .bind('open', =>
      this.show()
    )

    .bind('showEditor', (ctx, tag) =>
      this.show()
    )

    .bind('showAnnotations', (ctx, tags=[]) =>
      this.show()
      $rootScope.$emit('showAnnotations', tags)
    )

    .bind('focusAnnotations', (ctx, tags=[]) =>
      $rootScope.$emit('focusAnnotations', tags)
    )

    .bind('toggleAnnotationSelection', (ctx, tags=[]) =>
      $rootScope.$emit('toggleViewerSelection', tags)
    )

    .bind('setTool', (ctx, name) =>
      this.setTool(name)
    )

    .bind('setVisibleHighlights', (ctx, state) =>
      this.setVisibleHighlights(state)
    )

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

  setTool: (name) ->
    return if name is @tool
    @tool = name
    this.publish 'setTool', name
    for p in @providers
      p.channel.notify
        method: 'setTool'
        params: name

  setVisibleHighlights: (state) ->
    return if state is @visibleHighlights
    @visibleHighlights = state
    this.publish 'setVisibleHighlights', state
    for p in @providers
      p.channel.notify
        method: 'setVisibleHighlights'
        params: state

angular.module('h').service('crossFrameUI', CrossFrameUI)
