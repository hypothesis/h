# Instantiates all objects used for cross frame discovery and communication.
class CrossFrameService
  providers: null

  this.inject = [
    '$rootScope', '$document', '$window', 'store', 'annotationUI'
    'Discovery', 'bridge',
    'AnnotationSync', 'AnnotationUISync', 'host'
  ]
  constructor: (
    $rootScope, $document, $window, store, annotationUI
    Discovery, bridge,
    AnnotationSync, AnnotationUISync, host
  ) ->
    @providers = []

    createDiscovery = ->
      options =
        server: true
      new Discovery($window, options)

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
        emit: (args...) ->
          $rootScope.$apply ->
            $rootScope.$emit.call($rootScope, args...)
        on: (event, handler) ->
          $rootScope.$apply ->
            $rootScope.$on(event, (event, args...) -> handler.apply(this, args))

      new AnnotationSync(bridge, options)

    createAnnotationUISync = (bridge, annotationSync) ->
      new AnnotationUISync($rootScope, $window, bridge, annotationSync, annotationUI, host)

    addProvider = (channel) =>
      provider = {channel: channel, entities: []}

      channel.call
        method: 'getDocumentInfo'
        success: (info) =>
          $rootScope.$apply =>
            provider.entities = (link.href for link in info.metadata.link)
            @providers.push(provider)

    this.connect = ->
      discovery = createDiscovery()

      bridge.onConnect(addProvider)
      host.setBridge bridge
      annotationSync = createAnnotationSync(bridge)
      annotationUISync = createAnnotationUISync(bridge, annotationSync)

      onDiscoveryCallback = (source, origin, token) ->
        bridge.createChannel(source, origin, token)
      discovery.startDiscovery(onDiscoveryCallback)

      this.notify = bridge.notify.bind(bridge)

    this.notify = -> throw new Error('connect() must be called before notify()')

angular.module('h').service('crossframe', CrossFrameService)
