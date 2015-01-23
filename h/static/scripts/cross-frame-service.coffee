# Instantiates all objects used for cross frame discovery and communication.
class CrossFrameService
  providers: null

  this.inject = ['$rootScope', '$document', '$window', 'store', 'annotationUI']
  constructor: ($rootScope, $document, $window, store, annotationUI) ->
    @providers = []

    createDiscovery = ->
      options =
        server: true
      new CrossFrameDiscovery(options)

    # Set up the bridge plugin, which bridges the main annotation methods
    # between the host page and the panel widget.
    createBridge = ->
      options =
        scope: 'annotator:bridge'
      new CrossFrameBridge(options)

    createAnnotationSync = (bridge) ->
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

    createAnnotationUISync = (bridge) ->
      new AnnotationUISync($rootScope, $window, bridge, annotationUI)

    addProvider = (channel) =>
      provider = {channel: channel, entities: []}

      channel.call
        method: 'getDocumentInfo'
        success: (info) =>
          provider.entities = (link.href for link in info.metadata.link)
          @providers.push(provider)
          $rootScope.$emit('getDocumentInfo')

    this.connect = ->
      discovery = createDiscovery()
      bridge = createBridge()

      bridge.onConnect(addProvider)
      annotationSync = createAnnotationSync(bridge)
      annotationUISync = createAnnotationUISync(bridge)

      onDiscoveryCallback = (source, origin, token) =>
        bridge.createChannel(source, origin, token)
      discovery.startDiscovery(onDiscoveryCallback)

      this.notify = bridge.notify.bind(bridge)

    this.notify = -> throw new Error('connect() must be called before notify()')

run = ['crossframe', (crossframe) -> crossframe.connect()]

angular.module('h').service('crossframe', CrossFrameService).run(run)
