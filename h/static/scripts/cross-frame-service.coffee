# Instantiates all objects used for cross frame discovery and communication.
class CrossFrameService
  providers: null

  this.inject = ['$rootScope', '$document', '$window', 'store', 'annotationUI']
  constructor: ($rootScope, $document, $window, store, annotationUI) ->
    @providers = []

    # Set up the bridge plugin, which bridges the main annotation methods
    # between the host page and the panel widget.
    createBridge = ->
      options =
        gateway: true # TODO: Gerben, where does this go now?
      new CrossFrameBridge(options)

    createAnnotationSync = ->
      whitelist = ['target', 'document', 'uri']
      options =
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
      new AnnotationSync($rootScope, options, bridge)

      createAnnotationUISync = ->
        new AnnotationUISync($rootScope, $window, bridge, annotationUI)

      # TODO: This now needs to be called or passed to discovery.
      onConnect = (channel, source) =>
        provider = {channel: channel, entities: []}

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
            params: annotationUI.tool

          channel.notify
            method: 'setVisibleHighlights'
            params: annotationUI.visibleHighlights

    this.connect = ->
      bridge = createBridge()
      annotationSync = createAnnotationSync()
      annotationUISync = createAnnotationUISync()

      this.notify = bridge.notify.bind(bridge)

    this.notify = -> throw new Error('connect() must be called before notify()')

run = ['crossframe', (crossframe) -> crossframe.connect()]

angular.module('h').service('crossframe', CrossFrameService).run(run)
